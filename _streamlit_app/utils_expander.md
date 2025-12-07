Dieser Prototyp ist Teil eines Projekts vom Statistischen Amt, Kanton Zürich. Mit diesem Projekt möchten wir öffentliche Organisationen dabei unterstützen, ihre Kommunikation noch verständlicher aufzubereiten.

## Wichtig

- **:red[Nutze die App nur für öffentliche, nicht sensible Daten.]**
- **:red[Die App liefert lediglich einen Entwurf. Überprüfe das Ergebnis immer – idealerweise mit Menschen aus dem Zielpublikum – und passe es an, wenn nötig.]**

## Was macht diese App?

**Diese App übersetzt einen von dir eingegebenen Text in einen Entwurf für Einfache Sprache oder Leichte Sprache.**

Dein Text wird dazu in der App aufbereitet und an ein sogenanntes grosses Sprachmodell (LLM, Large Language Model) eines kommerziellen Anbieters geschickt. Diese Sprachmodelle sind in der Lage, Texte nach Anweisungen umzuformulieren und dabei zu vereinfachen.

Du kannst die Texte nach den Regeln für Einfache Sprache oder Leichte Sprache übersetzen.

- **Leichte Sprache** ist eine vereinfachte Form der deutschen Sprache, die nach bestimmten Regeln gestaltet wird. Leichte Sprache hilft u.a. Menschen mit Lernschwierigkeiten oder geringen Deutschkenntnissen.
- **Einfache Sprache** ist eine vereinfachte Version von Alltagssprache. Diese zielt darauf, Texte generell für ein breiteres Publikum verständlicher zu machen.

In der Grundeinstellung übersetzt die App in Einfache Spache. Wenn du den Schalter «Leichte Sprache» klickst, weist du die App an, einen Entwurf in **Leichter Sprache** zu schreiben. Wenn Leichte Sprache aktiviert ist, kannst du zusätzlich wählen, ob das Modell alle Informationen übernehmen oder versuchen soll, sinnvoll zu verdichten.

**Die Texte werden teils in sehr guter Qualität vereinfacht. Sie sind aber nie 100% korrekt. Die App liefert lediglich einen Entwurf. Die Texte müssen immer von dir überprüft und angepasst werden.** Insbesondere bei Leichter Sprache ist die Überprüfung der Ergebnisse durch Prüferinnen und Prüfer aus dem Zielpublikum essentiell.

### Wie funktioniert die Bewertung der Verständlichkeit?

Wir haben einen Algorithmus entwickelt, der die Verständlichkeit von Texten auf einer Skala von -10 bis 10 bewertet. Dieser Algorithmus basiert auf diversen Textmerkmalen: Den Wort- und Satzlängen, dem [Lesbarkeitsindex RIX](https://www.jstor.org/stable/40031755), der Häufigkeit von einfachen, verständlichen, viel genutzten Worten, sowie dem Anteil an Worten aus dem Standardvokabular A1, A2 und B1. Wir haben dies systematisch ermittelt, indem wir geschaut haben, welche Merkmale am aussagekräftigsten für Verwaltungs- und Rechtssprache und deren Vereinfachung sind.

Die Bewertung kannst du so interpretieren:

- **Sehr schwer verständliche Texte** wie Rechts- oder Verwaltungstexte haben meist Werte von **-10 bis -2**.
- **Durchschnittlich verständliche Texte** wie Nachrichtentexte, Wikipediaartikel oder Bücher haben meist Werte von **-2 bis 0**.
- **Gut verständliche Texte im Bereich Einfacher Sprache und Leichter Sprache** haben meist Werte von **0 oder grösser.**.

Wir zeigen dir zusätzlich eine **grobe** Schätzung des Sprachniveaus gemäss [CEFR (Common European Framework of Reference for Languages)](https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions) von A1 bis C2 an.

ADD_IMAGE_HERE

Die Bewertung ist bei weitem nicht perfekt, aber sie ist ein guter erster Anhaltspunkt und hat sich bei unseren Praxistests bewährt.

### Feedback

Wir sind für Rückmeldungen und Anregungen jeglicher Art dankbar und nehmen diese jederzeit gern [per Mail entgegen](mailto:datashop@statistik.zh.ch).

## Versionsverlauf

- **v1.1** - 07.12.2025 - _App aktualisiert auf neueste Modelle. Kleinere Verbesserungen._
- **v1.0** - 13.07.2025 - _App aktualisiert und umgeschrieben auf OpenRouter. Ältere App-Versionen entfernt bis auf Version OpenAI._
- **v0.8** - 07.06.2025 - _Modelle aktualisiert. Bugfixes._
- **v0.7** - 18.04.2025 - _Modelle aktualisiert. GPT-4.1 und GPT-4.1 mini, neue Gemini-Modelle. Refactoring zu aktuellem Google GenAI Python SDK._
- **v0.6** - 29.03.2025 - _Modelle aktualisiert._
- **v0.5** - 22.12.2024 - _Modelle aktualisiert und ergänzt. Code vereinfacht._
- **v0.4** - 30.08.2024 - _Fehler behoben._
- **v0.3** - 18.08.2024 - _Neuen ZIX-Index integriert. Diverse Fehler behoben._
- **v0.2** - 21.06.2024 - _Update auf Claude Sonnet v3.5._
- **v0.1** - 01.06.2024 - _Erste Open Source-Version der App auf Basis des bisherigen Pilotprojekts._
