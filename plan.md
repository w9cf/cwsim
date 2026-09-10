# Piano di Sviluppo Cwsim - Prossime Versioni

## UI & Accessibilità
- [ ] **Revisione Grid Layout Parametri**: Verificare il posizionamento dei nuovi parametri DX (Straight Key, My RST Speed-up, ecc.). Attualmente NVDA li riporta in fondo alla lista.
- [ ] **Tab Order**: Ottimizzare l'ordine dei tab affinché ogni Label sia seguita immediatamente dalla sua SpinBox, migliorando l'esperienza per utenti con screen reader.
- [ ] **Verifica Visiva**: Confermare se il layout è corretto anche visivamente o se i nuovi widget sono stati accodati in modo disordinato.

## Report & Logica DX
- [ ] **Pulizia Report in Modalità Expedition**: In modalità DX Expedition, rimuovere o nascondere i riferimenti ai "progressivi" (numeri seriali) nel report finale (`cwsim.txt`), dato che lo scambio prevede solo l'RST.
- [ ] **RST Validation**: Assicurarsi che la validazione dei dati nel report rifletta correttamente lo scambio 5NN unico della modalità DX.

## Manutenzione
- [ ] **Compilazione Traduzioni**: Produrre il file `.qm` aggiornato non appena l'ambiente dispone di `lrelease` o caricarlo manualmente.
- [ ] **Sincronizzazione Versioning**: Coordinarsi con Kevin per la numerazione ufficiale post-1.0.2.
