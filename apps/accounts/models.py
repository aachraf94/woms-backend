from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class CustomUser(AbstractUser):
    """Modèle utilisateur personnalisé avec noms de champs en français."""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrateur')
        MANAGER = 'MANAGER', _('Gestionnaire')
        OPERATOR = 'OPERATOR', _('Opérateur')
        SUPERVISOR = 'SUPERVISOR', _('Superviseur')
        ENGINEER = 'ENGINEER', _('Ingénieur')
        VIEWER = 'VIEWER', _('Visualiseur')
    
    # Champs principaux en français
    email = models.EmailField(unique=True, verbose_name=_('Email'))
    entreprise = models.CharField(max_length=255, blank=True, verbose_name=_('Entreprise'))
    fonction = models.CharField(max_length=255, blank=True, verbose_name=_('Fonction'))
    est_actif = models.BooleanField(default=True, verbose_name=_('Est actif'))
    telephone = models.CharField(max_length=20, blank=True, verbose_name=_('Téléphone'))
    date_derniere_connexion = models.DateTimeField(null=True, blank=True, verbose_name=_('Dernière connexion'))
    
    # Champ rôle avec choix en français
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        verbose_name=_('Rôle')
    )
    
    # Champs de compatibilité descendante (mappés automatiquement)
    @property
    def company(self):
        return self.entreprise
    
    @company.setter
    def company(self, value):
        self.entreprise = value
    
    @property
    def function(self):
        return self.fonction
    
    @function.setter
    def function(self, value):
        self.fonction = value
    
    @property
    def is_active(self):
        return self.est_actif
    
    @is_active.setter
    def is_active(self, value):
        self.est_actif = value
    
    # Utiliser l'email comme champ de connexion
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def mettre_a_jour_derniere_connexion(self):
        """Met à jour la date de dernière connexion."""
        self.date_derniere_connexion = timezone.now()
        self.save(update_fields=['date_derniere_connexion'])
        
    @classmethod
    def create_admin_user(cls, email, password, first_name='', last_name='', **extra_fields):
        """Méthode d'aide pour créer un utilisateur administrateur."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        extra_fields.setdefault('role', cls.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Définir le nom d'utilisateur comme étant le même que l'email s'il n'est pas fourni
        if 'username' not in extra_fields:
            extra_fields['username'] = email.split('@')[0]
        
        user = User.objects.create_user(
            email=email, 
            password=password,
            first_name=first_name, 
            last_name=last_name, 
            **extra_fields
        )
        return user

    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        ordering = ['last_name', 'first_name']


class FournisseurService(models.Model):
    """Modèle pour les fournisseurs de services avec noms de champs en français."""
    
    # Relations
    utilisateur = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name=_('Utilisateur'),
        related_name='fournisseur_service'
    )
    
    # Champs en français
    type_service = models.CharField(max_length=100, verbose_name=_('Type de service'))
    numero_contrat = models.CharField(max_length=50, unique=True, verbose_name=_('Numéro de contrat'))
    date_validite = models.DateField(verbose_name=_('Date de validité'))
    entreprise = models.CharField(max_length=255, verbose_name=_('Entreprise'))
    specialites = models.TextField(blank=True, verbose_name=_('Spécialités'))
    statut_actif = models.BooleanField(default=True, verbose_name=_('Statut actif'))
    
    # Champs d'audit
    cree_le = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    mis_a_jour_le = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))
    
    def __str__(self):
        return f"{self.utilisateur.get_full_name()} - {self.type_service}"
    
    @property
    def est_valide(self):
        """Vérifie si le contrat est encore valide."""
        return self.date_validite >= timezone.now().date()
    
    class Meta:
        verbose_name = _('Fournisseur de service')
        verbose_name_plural = _('Fournisseurs de service')
        ordering = ['entreprise', 'type_service']


class ProfilUtilisateur(models.Model):
    """Profil utilisateur étendu avec noms de champs en français."""
    
    # Relation
    utilisateur = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name=_('Utilisateur'),
        related_name='profil'
    )
    
    # Champs en français
    photo_profil = models.ImageField(
        upload_to='profils/', 
        blank=True, 
        null=True, 
        verbose_name=_('Photo de profil')
    )
    biographie = models.TextField(blank=True, verbose_name=_('Biographie'))
    experience_annees = models.PositiveIntegerField(default=0, verbose_name=_('Années d\'expérience'))
    certifications = models.TextField(blank=True, verbose_name=_('Certifications'))
    preferences_notification = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name=_('Préférences de notification')
    )
    langue_preferee = models.CharField(
        max_length=10, 
        default='fr',
        choices=[
            ('fr', _('Français')),
            ('en', _('Anglais')),
            ('ar', _('Arabe')),
        ],
        verbose_name=_('Langue préférée')
    )
    
    # Informations de localisation
    ville = models.CharField(max_length=100, blank=True, verbose_name=_('Ville'))
    pays = models.CharField(max_length=100, blank=True, verbose_name=_('Pays'))
    code_postal = models.CharField(max_length=20, blank=True, verbose_name=_('Code postal'))
    
    # Champs d'audit
    cree_le = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    mis_a_jour_le = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))
    
    def __str__(self):
        return f"Profil de {self.utilisateur.get_full_name()}"
    
    class Meta:
        verbose_name = _('Profil utilisateur')
        verbose_name_plural = _('Profils utilisateurs')


class JournalConnexion(models.Model):
    """Journal des connexions utilisateur pour audit et sécurité."""
    
    # Relation
    utilisateur = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name=_('Utilisateur'),
        related_name='journaux_connexion'
    )
    
    # Champs en français
    adresse_ip = models.GenericIPAddressField(verbose_name=_('Adresse IP'))
    user_agent = models.TextField(verbose_name=_('User Agent'))
    date_connexion = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de connexion'))
    date_deconnexion = models.DateTimeField(null=True, blank=True, verbose_name=_('Date de déconnexion'))
    duree_session = models.DurationField(null=True, blank=True, verbose_name=_('Durée de session'))
    type_connexion = models.CharField(
        max_length=20,
        choices=[
            ('WEB', _('Web')),
            ('MOBILE', _('Mobile')),
            ('API', _('API')),
        ],
        default='WEB',
        verbose_name=_('Type de connexion')
    )
    succes_connexion = models.BooleanField(default=True, verbose_name=_('Succès de connexion'))
    
    def __str__(self):
        return f"Connexion de {self.utilisateur.get_full_name()} - {self.date_connexion}"
    
    def terminer_session(self):
        """Termine la session et calcule la durée."""
        if not self.date_deconnexion:
            self.date_deconnexion = timezone.now()
            self.duree_session = self.date_deconnexion - self.date_connexion
            self.save(update_fields=['date_deconnexion', 'duree_session'])
    
    class Meta:
        verbose_name = _('Journal de connexion')
        verbose_name_plural = _('Journaux de connexion')
        ordering = ['-date_connexion']


class TokenJWT(models.Model):
    """Modèle pour le suivi des tokens JWT (pour la liste noire et l'audit)."""
    
    # Relation
    utilisateur = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_('Utilisateur'),
        related_name='tokens_jwt'
    )
    
    # Champs en français
    jti = models.CharField(max_length=255, unique=True, verbose_name=_('ID Token JWT'))
    type_token = models.CharField(
        max_length=20,
        choices=[
            ('ACCESS', _('Token d\'accès')),
            ('REFRESH', _('Token de rafraîchissement')),
        ],
        verbose_name=_('Type de token')
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_expiration = models.DateTimeField(verbose_name=_('Date d\'expiration'))
    est_sur_liste_noire = models.BooleanField(default=False, verbose_name=_('Est sur liste noire'))
    date_mise_liste_noire = models.DateTimeField(null=True, blank=True, verbose_name=_('Date mise liste noire'))
    adresse_ip = models.GenericIPAddressField(verbose_name=_('Adresse IP'))
    
    def __str__(self):
        return f"Token {self.type_token} - {self.utilisateur.email}"
    
    def mettre_sur_liste_noire(self):
        """Met le token sur la liste noire."""
        self.est_sur_liste_noire = True
        self.date_mise_liste_noire = timezone.now()
        self.save(update_fields=['est_sur_liste_noire', 'date_mise_liste_noire'])
    
    @property
    def est_expire(self):
        """Vérifie si le token est expiré."""
        return timezone.now() > self.date_expiration
    
    class Meta:
        verbose_name = _('Token JWT')
        verbose_name_plural = _('Tokens JWT')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['jti']),
            models.Index(fields=['utilisateur', 'type_token']),
            models.Index(fields=['est_sur_liste_noire']),
        ]
