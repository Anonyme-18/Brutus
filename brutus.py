import zipfile
import string
import itertools
import threading
import time
import os
import pygame
import io
import tempfile

class ZipCracker:
    def __init__(self):
        self.zip_file = None
        self.caracteres = string.ascii_lowercase + string.digits  # lettres minuscules et chiffres
        self.tentatives = 0
        self.mot_de_passe_trouve = None
        self.en_cours = False
        self.temps_debut = 0
        self.temps_ecoule = 0
        self.longueur_courante = 1
        self.tentatives_par_seconde = 0
        self.thread = None
        self.temp_dir = tempfile.mkdtemp()  # Dossier temporaire pour les tests

    def charger_fichier(self, nom_fichier):
        """Charge le fichier ZIP à cracker"""
        try:
            self.zip_file = zipfile.ZipFile(nom_fichier)
            return True
        except (zipfile.BadZipFile, FileNotFoundError) as e:
            return False

    def tester_mot_de_passe(self, mot_de_passe):
        """Teste un mot de passe sur le fichier ZIP avec une vérification stricte"""
        try:
            # Méthode plus stricte : essayer d'extraire TOUS les fichiers dans un dossier temporaire
            temp_extract_dir = os.path.join(self.temp_dir, "extract_test")
            os.makedirs(temp_extract_dir, exist_ok=True)
            
            # Nettoyer le dossier de test
            for file in os.listdir(temp_extract_dir):
                os.remove(os.path.join(temp_extract_dir, file))
            
            # Tenter l'extraction complète
            self.zip_file.extractall(path=temp_extract_dir, pwd=mot_de_passe.encode())
            
            # Vérifier si l'extraction a bien créé des fichiers
            extracted_files = os.listdir(temp_extract_dir)
            if not extracted_files:
                return False
            
            # Vérifier que les fichiers sont valides
            for file in extracted_files:
                file_path = os.path.join(temp_extract_dir, file)
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    return False
            
            return True
        except Exception as e:
            return False

    def generer_mots_de_passe(self):
        """Générateur de mots de passe par force brute"""
        max_length = 8  # Limite la longueur maximale pour éviter des recherches infinies
        
        while self.en_cours and self.longueur_courante <= max_length:
            print(f"Essai avec longueur: {self.longueur_courante}")
            for mot_de_passe in itertools.product(self.caracteres, repeat=self.longueur_courante):
                if not self.en_cours:
                    return
                
                self.tentatives += 1
                mot_de_passe_str = ''.join(mot_de_passe)
                
                # Log périodique pour debugging
                if self.tentatives % 1000 == 0:
                    print(f"Tentative: {self.tentatives}, Test: {mot_de_passe_str}")
                
                # Calcul du taux de tentatives par seconde
                temps_actuel = time.time()
                if temps_actuel - self.temps_debut >= 1:
                    self.tentatives_par_seconde = self.tentatives / (temps_actuel - self.temps_debut)
                
                if self.tester_mot_de_passe(mot_de_passe_str):
                    print(f"MOT DE PASSE TROUVÉ: {mot_de_passe_str}")
                    self.mot_de_passe_trouve = mot_de_passe_str
                    self.en_cours = False
                    return
            
            # Augmenter la longueur si tous les mots de passe de la longueur actuelle ont été essayés
            self.longueur_courante += 1
            print(f"Passage à la longueur: {self.longueur_courante}")

    def demarrer_craquage(self):
        """Démarre le processus de craquage dans un thread séparé"""
        if not self.en_cours and self.zip_file:
            self.en_cours = True
            self.tentatives = 0
            self.mot_de_passe_trouve = None
            self.temps_debut = time.time()
            self.thread = threading.Thread(target=self.generer_mots_de_passe)
            self.thread.daemon = True
            self.thread.start()

    def arreter_craquage(self):
        """Arrête le processus de craquage"""
        self.en_cours = False
        if self.thread:
            self.thread.join(timeout=1)
        self.temps_ecoule = time.time() - self.temps_debut


class Interface:
    def __init__(self):
        pygame.init()
        self.largeur, self.hauteur = 800, 600
        self.ecran = pygame.display.set_mode((self.largeur, self.hauteur))
        pygame.display.set_caption("Craqueur de ZIP")
        
        self.cracker = ZipCracker()
        self.police = pygame.font.SysFont('Arial', 24)
        self.police_petite = pygame.font.SysFont('Arial', 18)
        self.police_grande = pygame.font.SysFont('Arial', 28, bold=True)
        
        self.nom_fichier = ""
        self.saisie_active = True
        self.couleur_fond = (30, 30, 30)
        self.couleur_texte = (255, 255, 255)
        self.couleur_input = (50, 50, 50)
        self.couleur_bouton = (70, 130, 180)
        self.couleur_bouton_hover = (100, 160, 210)
        self.message = "Entrez le nom du fichier ZIP à cracker"
        
        self.bouton_charger = pygame.Rect(300, 150, 200, 50)
        self.bouton_demarrer = pygame.Rect(300, 250, 200, 50)
        self.bouton_arreter = pygame.Rect(300, 350, 200, 50)
        
        self.fichier_charge = False
        self.running = True

    def afficher_texte(self, texte, position, police=None, couleur=None):
        """Affiche du texte à l'écran"""
        if police is None:
            police = self.police
        if couleur is None:
            couleur = self.couleur_texte
            
        surface_texte = police.render(texte, True, couleur)
        rect_texte = surface_texte.get_rect(center=position)
        self.ecran.blit(surface_texte, rect_texte)

    def boucle_principale(self):
        """Boucle principale de l'interface"""
        input_rect = pygame.Rect(250, 100, 300, 40)
        clock = pygame.time.Clock()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.cracker.arreter_craquage()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Vérification des clics sur les boutons
                    if self.bouton_charger.collidepoint(event.pos):
                        self.charger_fichier()
                    elif self.bouton_demarrer.collidepoint(event.pos) and self.fichier_charge:
                        self.cracker.demarrer_craquage()
                    elif self.bouton_arreter.collidepoint(event.pos):
                        self.cracker.arreter_craquage()
                    
                    # Activation/désactivation de la saisie
                    self.saisie_active = input_rect.collidepoint(event.pos)
                
                if event.type == pygame.KEYDOWN and self.saisie_active:
                    if event.key == pygame.K_RETURN:
                        self.charger_fichier()
                    elif event.key == pygame.K_BACKSPACE:
                        self.nom_fichier = self.nom_fichier[:-1]
                    else:
                        self.nom_fichier += event.unicode
            
            # Mise à jour des informations
            if self.cracker.en_cours:
                self.cracker.temps_ecoule = time.time() - self.cracker.temps_debut
            
            # Affichage
            self.ecran.fill(self.couleur_fond)
            
            # Affichage du champ de saisie
            pygame.draw.rect(self.ecran, self.couleur_input, input_rect)
            if self.saisie_active:
                pygame.draw.rect(self.ecran, (100, 100, 200), input_rect, 2)
            else:
                pygame.draw.rect(self.ecran, (70, 70, 70), input_rect, 2)
            
            # Affichage du texte saisi
            self.afficher_texte(self.nom_fichier, (input_rect.centerx, input_rect.centery))
            
            # Affichage du message d'instruction
            self.afficher_texte(self.message, (self.largeur // 2, 50))
            
            # Affichage des boutons
            mouse_pos = pygame.mouse.get_pos()
            
            # Bouton Charger
            couleur_bouton_charger = self.couleur_bouton_hover if self.bouton_charger.collidepoint(mouse_pos) else self.couleur_bouton
            pygame.draw.rect(self.ecran, couleur_bouton_charger, self.bouton_charger, border_radius=5)
            self.afficher_texte("Charger fichier", (self.bouton_charger.centerx, self.bouton_charger.centery))
            
            # Bouton Démarrer
            couleur_bouton_demarrer = self.couleur_bouton if not self.fichier_charge else (
                self.couleur_bouton_hover if self.bouton_demarrer.collidepoint(mouse_pos) else self.couleur_bouton
            )
            pygame.draw.rect(self.ecran, couleur_bouton_demarrer, self.bouton_demarrer, border_radius=5)
            self.afficher_texte("Démarrer craquage", (self.bouton_demarrer.centerx, self.bouton_demarrer.centery))
            
            # Bouton Arrêter
            couleur_bouton_arreter = (
                self.couleur_bouton_hover if self.bouton_arreter.collidepoint(mouse_pos) else self.couleur_bouton
            )
            pygame.draw.rect(self.ecran, couleur_bouton_arreter, self.bouton_arreter, border_radius=5)
            self.afficher_texte("Arrêter craquage", (self.bouton_arreter.centerx, self.bouton_arreter.centery))
            
            # Affichage des statistiques
            if self.fichier_charge:
                y_pos = 430
                
                self.afficher_texte(f"Fichier chargé: {self.nom_fichier}", 
                                  (self.largeur // 2, y_pos), self.police_petite)
                y_pos += 30
                
                if self.cracker.en_cours:
                    etat = "En cours..."
                    couleur_etat = (0, 255, 0)
                elif self.cracker.mot_de_passe_trouve:
                    etat = "Mot de passe trouvé!"
                    couleur_etat = (0, 255, 0)
                else:
                    etat = "En attente"
                    couleur_etat = (255, 255, 0)
                
                self.afficher_texte(f"État: {etat}", (self.largeur // 2, y_pos), 
                                  self.police_petite, couleur_etat)
                y_pos += 30
                
                # Affichage séparé et plus visible du mot de passe trouvé
                if self.cracker.mot_de_passe_trouve:
                    self.afficher_texte(f"MOT DE PASSE: {self.cracker.mot_de_passe_trouve}", 
                                      (self.largeur // 2, y_pos), self.police_grande, (255, 215, 0))  # Or
                    y_pos += 40  # Espacement plus grand
                
                self.afficher_texte(f"Tentatives: {self.cracker.tentatives}", 
                                  (self.largeur // 2, y_pos), self.police_petite)
                y_pos += 30
                
                self.afficher_texte(f"Longueur actuelle: {self.cracker.longueur_courante} caractères", 
                                  (self.largeur // 2, y_pos), self.police_petite)
                y_pos += 30
                
                self.afficher_texte(f"Temps écoulé: {self.cracker.temps_ecoule:.2f} secondes", 
                                  (self.largeur // 2, y_pos), self.police_petite)
                y_pos += 30
                
                if self.cracker.tentatives_par_seconde > 0:
                    self.afficher_texte(f"Vitesse: {self.cracker.tentatives_par_seconde:.2f} tentatives/sec", 
                                      (self.largeur // 2, y_pos), self.police_petite)
            
            pygame.display.flip()
            clock.tick(30)
    
    def charger_fichier(self):
        """Charge le fichier ZIP spécifié"""
        if os.path.exists(self.nom_fichier) and self.nom_fichier.endswith('.zip'):
            if self.cracker.charger_fichier(self.nom_fichier):
                self.fichier_charge = True
                self.message = f"Fichier '{self.nom_fichier}' chargé avec succès"
            else:
                self.message = f"Erreur: Le fichier '{self.nom_fichier}' est invalide"
        else:
            self.message = f"Erreur: Le fichier '{self.nom_fichier}' n'existe pas ou n'est pas un ZIP"


if __name__ == "__main__":
    interface = Interface()
    try:
        interface.boucle_principale()
    finally:
        pygame.quit()