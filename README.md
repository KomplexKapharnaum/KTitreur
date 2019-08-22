# KTitreur
## KXKM Titreurs

Run client on Titreur:
`python ./titreur/main.py [UDP port = 3742]`

Run controller on Desktop:
`./regie-start`

MAIN REGIE keyboard controller:
- CTRL + Arrow RIGHT / PageUp  = Mode Fx
- CTRL + Arrow DOWN  / Home    = Mode FreeType
- CTRL + Arrow LEFT  / Insert  = Mode Playlist
- Arrow UP    / End             = Clear All
- F1 - F8                       = Select Titreur
- F9                            = Inverse selection
- F12                           = Select All / None


Mode FX:
- Choose FX from 0 to 9
- FX scenarios are editable files in fx/ folder

Mode FREETYPE:
- Typed text is displayed live on selected Titreurs
- Backspace to live erase characters
- Enter to clear the text

Mode PLAYLIST:
- Type and Enter to add text to Titreurs playlist
- Playlist items are rotated randomly with random delay (min, max) called speed in milliseconds
- Send `>> 1000` to change text rotation speed to i.e. 1000ms

RETOUR USER : 
Séparer dans le mode Freetype le scroll et le texte fixe en 2 modes distincts. 
- Playlist items are rotated randomly with delay called speed in milliseconds
- Send `>1000` to change text rotation speed to i.e. 1000ms

