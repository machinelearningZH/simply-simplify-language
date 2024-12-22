Dieser Prototyp ist Teil eines Projekts vom Statistischen Amt, Kanton Zürich. Mit diesem Projekt möchten wir öffentliche Organisationen dabei unterstützen, ihre Kommunikation noch verständlicher aufzubereiten.

## Wichtig

- **:red[Nutze die App nur für öffentliche, nicht sensible Daten.]**
- **:red[Die App liefert lediglich einen Entwurf. Überprüfe das Ergebnis immer – idealerweise mit Menschen aus dem Zielpublikum – und passe es an, wenn nötig.]**

## Was macht diese App?

**Diese App versucht, einen von dir eingegebenen Text in Einfache Sprache oder Leichte Sprache zu übersetzen.**

Dein Text wird dazu in der App aufbereitet und an ein sogenanntes grosses Sprachmodell (LLM, Large Language Model) eines kommerziellen Anbieters geschickt. Diese Sprachmodelle sind in der Lage, Texte nach Anweisungen umzuformulieren und dabei zu vereinfachen.

Du kannst die Texte nach den Regeln für Einfache Sprache oder Leichte Sprache übersetzen.

**Leichte Sprache** ist eine vereinfachte Form der deutschen Sprache, die nach bestimmten Regeln gestaltet wird. Leicht Sprache hilft u.a. Menschen mit Lernschwierigkeiten oder geringen Deutschkenntnissen.

**Einfache Sprache** ist eine vereinfachte Version von Alltagssprache. Diese zielt darauf, Texte generell für ein breiteres Publikum verständlicher zu machen.

**Die Texte werden teils in sehr guter Qualität vereinfacht. Sie sind aber nie 100% korrekt. Die App liefert lediglich einen Entwurf. Die Texte müssen immer von dir überprüft und angepasst werden. Insbesondere bei Leichter Sprache ist [die Überprüfung der Ergebnisse durch Prüferinnen und Prüfer aus dem Zielpublikum essentiell](https://www.leichte-sprache.org/leichte-sprache/das-pruefen/).**

### Modus «Leichte Sprache»?

In der Grundeinstellung übersetzt die App in Einfache Spache. Wenn du den Schalter «Leichte Sprache» klickst, weist du das Modell an, einen Entwurf in **Leichter Sprache** zu schreiben. Wenn Leichte Sprache aktiviert ist, kannst du zusätzlich wählen, ob das Modell alle Informationen übernehmen oder versuchen soll, sinnvoll zu verdichten.

### Was sind die verschiedenen Sprachmodelle?

Momentan kannst du eins von 11 Sprachmodellen wählen:

- **Mistral Nemo**: gute Qualität, 0.1 CHF
- **Mistral Large**: sehr gute Qualität, 2.2 CHF
- **Claude V3.5 Haiku**: sehr gute Qualität, 1.4 CHF
- **Claude V3.5 Sonnet**: beste Qualität, 5.1 CHF
- **GPT-4o mini**: gute Qualität, 0.2 CHF
- **GPT-4o**: sehr gute Qualität, 3.5 CHF
- **o1 mini**: [«Reasoning-Modell»](https://openai.com/o1/), beste Qualität, 5 CHF
- **o1**: [«Reasoning-Modell»](https://openai.com/o1/), beste Qualität, 25 CHF
- **Gemini 1.5 Flash**: gute Qualität, 0.15 CHF
- **Gemini 2.0 Flash**: sehr gute Qualität, 0.15 CHF
- **Gemini 1.5 Pro**: beste Qualität, 1.8 CHF

*(Ungefähre Kostengrössen für 100 [Normseiten](https://de.wikipedia.org/wiki/Normseite) á 250 Worten, Stand Dezember 2024, ohne Gewähr)*

Alle Modelle analysieren und schreiben unterschiedlich und sind alle einen Versuch wert. Die Claude-Modelle werden von [Anthropic](https://www.anthropic.com/) betrieben, die GPT- und o1-Modelle von [OpenAI](https://openai.com/), die Mistral-Modelle von [Mistral](https://mistral.ai/) und die Gemini-Modelle von [Google](https://ai.google.dev/).<br>

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

- **v0.5** - 22.12.2024 - *Modelle aktualisiert und ergänzt. Code vereinfacht.*
- **v0.4** - 30.08.2024 - *Fehler behoben.*
- **v0.3** - 18.08.2024 - *Neuen ZIX-Index integriert. Diverse Fehler behoben.*
- **v0.2** - 21.06.2024 - *Update auf Claude Sonnet v3.5.*
- **v0.1** - 1.06.2024 - *Erste Open Source-Version der App auf Basis des bisherigen Pilotprojekts.*
