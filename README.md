# VDLTools
Outils QGIS pour la Ville de Lausanne
-------------------------------------


- Duplicate

L'outil "Duplicate" permet de copier un objet dans une direction à une distance donnée. La distance est fixe pour chaque noeud de l'objet, donc la géométrie n'est pas conservée.
La couche de l'objet doit être éditable. Sélectionner l'objet d'un clic, puis choisir la distance et la direction.


- Move

L'outil "Move" permet de déplacer ou copier un objet.
La couche de l'objet doit être éditable. Sélectionner l'objet d'un clic. 
S'il ne s'agit pas d'un point, sélectionner ensuite d'un clic un vertex par lequelle vous voulez bouger l'objet.
Déplacer l'objet et cliquer pour fixer la position. Choisir entre le déplacement et la copie. En cas de copie, le formulaire des attributs est affiché avant l'enregistrement du nouvel objet.


- Intersect

L'outil "Intersect" permet de créer un cercle de construction d'un rayon donné. 
Il utilise 2 couches mémoire qu'il faut choisir dans la fenêtre des paramètres (accessible par le menu Extension->VDLTools).
Cliquer sur un point de centrage et choisir le diamètre.


- Profile

L'outil "Profile" permet d'afficher le profil d'une ligne 3D en parallèle de couches de points 3D.
Cliquer sur une première ligne (celle-ci déterminera le sens du profil), puis sur autant de lignes contiguës que nécessaire. Cliquer ensuite du bouton droit pour lancer le profil.
Choisir les couches de points à afficher. 2 librairies d'affichage sont à choix (à choisir avant la sélection des objets). 
Comme avantages, "Qwt5" permet de zoomer sur le profil, alors que "Matplotlib" permet de voir où on en est sur la carte en passant la souris sur le profil.


- Interpolate

L'outil "Interpolate" permet d'interpoler une altitude au milieu d'un segment, et d'y créer un nouveau vertex.
La couche de points doit être éditable (?). Cliquer en un point du segment, puis choisir entre un nouveau vertex pour la ligne, un nouveau point, ou les deux en même temps.


- Extrapolate

L'outil "Extrapolate" permet d'extrapoler une altitude en bout de ligne.
La couche de l'objet doit être éditable. Cliquer sur le vertex à extrapoler. 
Le segment reliant le vertex doit faire moins d'un quart du segment précédent sur la ligne pour pouvoir calculer une extrapolation.


- Import

L'outil "Import" permettra d'importer des données venant du terrain dans les différentes tables.



