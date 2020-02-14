# VDLTools
Outils QGIS pour la Ville de Lausanne
-------------------------------------


- Intersect

L'outil "Intersect" permet de créer un cercle de construction d'un rayon donné. 

    - sélectionner une couche
    - sélectionner l'outil
    - sélectionner une position (utilisation possible des options d'accrochage de la couche)
    - choisir le diamètre
    - en cliquant sur OK le point central est enregistré dans une couche mémoire de points et le cercle dans une couche mémoire de lignes
        ces couches peuvent être choisies dans la fenêtre des paramètres (accessible par le menu Extension->VDLTools)
        si aucune couche n'est séléctionnée, de nouvelles couches sont créées au moment de la création des premiers éléments

![Intersect Gif](./gifs/intersect.gif)

---

- Profile

L'outil "Profile" permet d'afficher le profil d'une ligne 3D en parallèle de couches de points 3D.

    - sélectionner une couche lignes
    - sélectionner l'outil
    - sélectionner la librairie d'affichage (2 à choix : "Qwt5" et "Matplotlib", la première par défaut. 
        Comme avantages, "Qwt5" permet de zoomer sur le profil, alors que "Matplotlib" permet de voir où on en est sur la carte en passant 
        la souris sur le profil.)
    - sélectionner une première ligne (celle-ci déterminera le sens du profil) avec le bouton gauche
    - sélectionner autant de lignes contiguës que nécessaire avec le bouton gauche
    - cliquer sur le bouton droit pour lancer le profil
    - choisir les couches de points à afficher (points, ou vertices de lignes ou de polygones)
    - si des altitudes ne correspondent pas entre les vertex de la lignes et les points, il est proposé de faire à choix : 
        appliquer l'altitude du vertex au point, appliquer l'altitude du point au vertex, ne rien faire
    - les altitudes nulles de la ligne qui n'ont aucun point de référence sont interpolées ou extrapolées, dans la mesure du possible.
        L'altitude des points présents sous lesdits vertices, si elles sont nulles, sont également modifiées.
    - il est également possible d'afficher le profil mnt si un service mapfish est disponible, qu'il faut mettre dans les paramètres

![Profile Gif](./gifs/profile.gif)

---

- Subprofile

L'outil "Subprofile" permet d'afficher le profil mnt, si un service mapfish est disponible, le long d'une polyline construite

---

- Interpolate

L'outil "Interpolate" permet d'interpoler une altitude au milieu d'un segment de ligne, et d'y créer un nouveau vertex et/ou un nouveau point.

    - sélectionner une couche points éditable
    - sélectionner l'outil
    - sélectionner la ligne sur laquelle se positionner
    - sélectionner une position (utilisation possible des options d'accrochage de la couche)
    - choisir si l'on veut créer un point, un vertex, ou les deux (si la position contient déjà un vertex : pas de choix, seul le point sera construit)
    - compléter les attributs du formulaire s'il est affiché    
    - cliquer à côté de la ligne pour la dé-sélectionner, ou sélectionner une nouvelle position sur cette ligne

![Interpolate Gif](./gifs/interpolate.gif)

---

- Extrapolate

L'outil "Extrapolate" permet d'extrapoler une altitude en bout de ligne.

    - sélectionner une couche lignes éditable
    - sélectionner l'outil
    - sélectionner une extrémité de ligne à extrapoler (le dernier segment ne doit pas faire plus d'un quart du segment précédent)
 
![Extrapolate Gif](./gifs/extrapolate.gif)   

---

- Pointer 

L'outil "Pointer" permet d'obtenir l'altitude de différents éléments en un point donné.

---

- Control

Utilisation du modèle de représentation "Contrôle"

Voir la démo ci-dessous

![Modèle représentation "Contrôle"](gifs/control_model_use.gif)

Utilisation de l'outil de contrôle du plugin "VDLNetwork"

Voir la démo ci-dessous


![Utilisation outils de contrôle (plugin)](gifs/control.gif)


