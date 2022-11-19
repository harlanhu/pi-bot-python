from core.devices import NixieTube

nixie_tube = NixieTube("test", 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 11, 12)
nixie_tube.display_content("DO not touch")
