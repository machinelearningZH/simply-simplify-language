Dieser Prototyp ist Teil eines Projekts vom Statistischen Amt, Kanton Zürich. Mit diesem Projekt möchten wir öffentliche Organisationen dabei unterstützen, ihre Kommunikation noch verständlicher aufzubereiten.

## Wichtig
- **:red[Nutze die App nur für öffentliche, nicht sensible Daten.]**
- **:red[Die App liefert lediglich einen Entwurf. Überprüfe das Ergebnis immer – idealerweise mit Menschen aus dem Zielpublikum – und passe es an, wenn nötig.]**


## Was macht diese App?

**Diese App übersetzt einen Text in Entwürfe für Einfache Sprache oder Leichte Sprache.**

Dein Text wird dazu in der App aufbereitet und an ein sogenanntes grosses Sprachmodell (LLM, Large Language Model) eines kommerziellen Anbieters geschickt. Diese Sprachmodelle sind in der Lage, Texte nach Anweisungen umzuformulieren und dabei zu vereinfachen.

**Die Texte werden teils in sehr guter Qualität vereinfacht. Sie sind aber nie 100% korrekt. Die App liefert lediglich einen Entwurf. Die Texte müssen immer von dir überprüft und angepasst werden. Insbesondere bei Leichter Sprache ist [die Überprüfung der Ergebnisse durch Prüferinnen und Prüfer aus dem Zielpublikum essentiell](https://www.leichte-sprache.org/leichte-sprache/das-pruefen/).**

### Was ist der Modus «Leichte Sprache»?
Mit dem Schalter «Leichte Sprache» kannst du das Modell anweisen, einen ***Entwurf*** in Leichter Sprache zu schreiben. Wenn Leichte Sprache aktiviert ist, kannst du zusätzlich wählen, ob das Modell alle Informationen übernehmen oder versuchen soll, sinnvoll zu verdichten. 


### Welches Sprachmodell wird verwendet?
In dieser App-Variante werden die Sprachmodelle Gemini 1.5 / 2.0 Flash und Gemini 1.5 Pro von [Google](https://deepmind.google/technologies/gemini/) verwendet.


### Wie funktioniert die Bewertung der Verständlichkeit?
Wir haben einen Algorithmus entwickelt, der die Verständlichkeit von Texten auf einer Skala von -10 bis 10 bewertet. Dieser Algorithmus basiert auf diversen Textmerkmalen: Den Wort- und Satzlängen, dem [Lesbarkeitsindex RIX](https://www.jstor.org/stable/40031755), der Häufigkeit von einfachen, verständlichen, viel genutzten Worten, sowie dem Anteil an Worten aus dem Standardvokabular A1, A2 und B1. Wir haben dies systematisch ermittelt, indem wir geschaut haben, welche Merkmale am aussagekräftigsten für Verwaltungs- und Rechtssprache und deren Vereinfachung sind.

Die Bewertung kannst du so interpretieren:

- **Sehr schwer verständliche Texte** wie Rechts- oder Verwaltungstexte haben meist Werte von **-10 bis -2**.
- **Durchschnittlich verständliche Texte** wie Nachrichtentexte, Wikipediaartikel oder Bücher haben meist Werte von **-2 bis 0**.
- **Gut verständliche Texte im Bereich Einfacher Sprache und Leichter Sprache** haben meist Werte von **0 oder grösser.**.

Wir zeigen dir zusätzlich eine **grobe** Schätzung des Sprachniveaus gemäss [CEFR (Common European Framework of Reference for Languages)](https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions) von A1 bis C2 an.  

### Image ###
Die Bewertung ist bei weitem nicht perfekt, aber sie ist ein guter erster Anhaltspunkt und hat sich bei unseren Praxistests bewährt.


### Feedback
Wir sind für Rückmeldungen und Anregungen jeglicher Art dankbar und nehmen diese jederzeit gern [per Mail entgegen](mailto:datashop@statistik.zh.ch).


## Versionsverlauf
- **v0.2** – 22.12.2024 – *Modelle aktualisiert und ergänzt: Gemini Flash 2.0. Code vereinfacht.*
- **v0.1** - 02.09.2024 - *App-Version für Google Gemini Modelle.*