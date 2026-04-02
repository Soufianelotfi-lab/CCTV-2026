# Installation & Configuration SSH — Multi-Cam Display

## ⚠️ IMPORTANT — SSH X11 Forwarding

Pour que l'application affiche sur l'écran DP-0 de la Jetson, vous **DEVEZ** vous connecter en SSH **avec X11 forwarding activé**.

### Étape 1 : Configuration SSH sur la Jetson

**Sur la Jetson**, éditez le fichier de configuration SSH:

```bash
sudo nano /etc/ssh/sshd_config
```

Assurez-vous que ces lignes sont **décommentées** et prennent ces valeurs:

```
X11Forwarding yes
X11DisplayOffset 10
X11UseLocalhost yes
PermitUserEnvironment yes
```

Redémarrez le service SSH:

```bash
sudo systemctl restart sshd
```

### Étape 2 : Connexion SSH depuis votre PC

**Depuis votre PC Linux/macOS/Windows (PowerShell/WSL)**:

```bash
# Option 1 : Forwarding X11 complet
ssh -X k-challenge@192.168.1.XXX

# Option 2 : Forwarding X11 de confiance (plus rapide)
ssh -Y k-challenge@192.168.1.XXX
```

Remplacez `192.168.1.XXX` par l'adresse IP de votre Jetson.

### Étape 3 : Vérifier que DISPLAY est correctement défini

Une fois connecté en SSH:

```bash
echo $DISPLAY
```

Vous devriez voir quelque chose comme:

```
localhost:10.0
```

Si c'est vide, la connexion n'a pas activé X11 forwarding. Reconnectez-vous avec l'option `-X` ou `-Y`.

### Étape 4 : Tester X11 avant de lancer l'app

Testez l'affichage X11:

```bash
# Cela devrait afficher un diagnostic de l'écran X11
xhost

# ou pour plus de détails:
xdpyinfo | head -10
```

Si vous voyez une erreur "unable to open display", c'est que X11 forwarding n'est pas actif.

## 🚀 Lancer l'application

Maintenant que X11 forwarding est configuré:

```bash
cd ~/multi_cam_display

# Mode automatique
./start.sh

# Mode verbose pour diagnostiquer les problèmes
./start.sh --verbose

# Ou directement lancez main.py
python3 main.py
```

L'application affichera le flux vidéo sur l'écran DP-0 de la Jetson en temps réel.

## 📊 Diagnostique système

Avant de lancer l'app, vous pouvez vérifier que tout est prêt:

```bash
bash ~/multi_cam_display/check_system.sh
```

Cela vérifie:
- ✓ Les 8 caméras ISX031
- ✓ Les plugins GStreamer
- ✓ Les fichiers Python
- ✓ La configuration X11  
- ✓ L'état global du système

## ⚠️ Dépannage SSH

### "unable to open display" depuis SSH

**Cause**: X11 forwarding n'est pas activé

**Solution**:
```bash
# Quittez SSH
exit

# Reconnectez-vous AVEC L'OPTION -X ou -Y
ssh -X k-challenge@192.168.1.XXX

# Vérifiez
echo $DISPLAY  # Doit afficher localhost:10.0
```

### SSH trop lent avec X11

Si X11 forwarding est très lent, essayez l'option `-C` (compression):

```bash
ssh -X -C k-challenge@192.168.1.XXX
```

### GStreamer affiche "Could not open DRM failed"

**Cause**: X11 forwarding n'a pas créé le fichier /dev/dri

**Solution**:
1. Vérifiez que vous utilisez ssh `-X` ou `-Y`
2. Redémarrez la session SSH
3. Vérifiez `ls /dev/dri/` — doit afficher des fichiers de périphérique

## 🔧 Configuration SSH avancée

### Pour les utilisateurs Windows (PowerShell/WSL)

Si vous utilisez Windows, installez d'abord un serveur X11 local (Xming, VcXsrv, etc), puis:

**PowerShell**:
```powershell
ssh -X k-challenge@jetson-ip
```

**WSL2 Ubuntu**:
```bash
export DISPLAY=:0
ssh -X k-challenge@jetson-ip
```

### SSH sans mot de passe (clé publique)

Pour éviter de taper le mot de passe à chaque connexion:

**Depuis votre PC**:
```bash
ssh-keygen -t rsa -b 4096
ssh-copy-id -i ~/.ssh/id_rsa.pub k-challenge@jetson-ip
```

Puis connectez-vous sans mot de passe:
```bash
ssh -X k-challenge@jetson-ip
```

### Alias SSH plus court

Ajoutez ceci à `~/.ssh/config` sur votre PC:

```
Host jetson
    HostName 192.168.1.XXX
    User k-challenge
    ForwardX11 yes
    ForwardX11Trusted yes
```

Puis connectez-vous simplement:

```bash
ssh jetson
```

## 📞 Vérification finale

Avant de déclarer le système "prêt", vérifiez:

| ✓ | Étape |
|---|---|
| ✓ | SSH connecté avec `ssh -X` ou `ssh -Y` |
| ✓ | `echo $DISPLAY` affiche `localhost:10.0` |
| ✓ | `xhost` fonctionne sans erreur |
| ✓ | `bash check_system.sh` retourne 0 erreurs |
| ✓ | Les 8 caméras sont détectées (`ls /dev/video*`) |
| ✓ | Les plugins GStreamer NVIDIA sont disponibles |
| ✓ | `./start.sh` lance l'app sans erreur |

Une fois tout cela OK, vous êtes prêt à utiliser le système multi-caméra ! 🎉
