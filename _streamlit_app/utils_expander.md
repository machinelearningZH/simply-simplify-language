Dieser Prototyp ist Teil eines Projekts vom Statistischen Amt, Kanton Zürich. Mit diesem Projekt möchten wir öffentliche Organisationen dabei unterstützen, ihre Kommunikation noch verständlicher aufzubereiten.

## Wichtig
- **:red[Nutze die App nur für öffentliche, nicht sensible Daten.]**
- **:red[Die App liefert lediglich einen Entwurf. Überprüfe das Ergebnis immer – idealerweise mit Menschen aus dem Zielpublikum – und passe es an, wenn nötig.]**


## Was macht diese App?

**Diese App versucht, einen von dir eingegebenen Text in Einfache Sprache oder Leichte Sprache zu übersetzen.**

Dein Text wird dazu in der App aufbereitet und an ein sogenanntes grosses Sprachmodell (LLM, Large Language Model) eines kommerziellen Anbieters geschickt. Diese Sprachmodelle sind in der Lage, Texte nach Anweisungen umzuformulieren und dabei zu vereinfachen.

**Die Texte werden teils in sehr guter Qualität vereinfacht. Sie sind aber nie 100% korrekt. Die App liefert lediglich einen Entwurf. Die Texte müssen immer von dir überprüft und angepasst werden. Insbesondere bei Leichter Sprache ist [die Überprüfung der Ergebnisse durch Prüferinnen und Prüfer aus dem Zielpublikum essentiell](https://www.leichte-sprache.org/leichte-sprache/das-pruefen/).**

### Was ist der Modus «Leichte Sprache»?
Mit dem Schalter «Leichte Sprache» kannst du das Modell anweisen, einen ***Entwurf*** in Leichter Sprache zu schreiben. Wenn Leichte Sprache aktiviert ist, kannst du zusätzlich wählen, ob das Modell alle Informationen übernehmen oder versuchen soll, sinnvoll zu verdichten. 


### Was sind die verschiedenen Sprachmodelle?
Momentan kannst du eins von 6 Sprachmodellen wählen:

- **Mistral Large**: sehr gute Qualität, 4.5 CHF
- **Claude V3 Haiku**: gute Qualität, 0.5 CHF
- **Claude V3 Sonnet**: sehr gute Qualität, 5.1 CHF
- **Claude V3 Opus**: beste Qualität, 25.5 CHF
- **GPT-4**: sehr gute Qualität, 11 CHF
- **GPT-4o**: beste Qualität, 5.5 CHF

*(Ungefähre Kostengrössen für 100 [Normseiten](https://de.wikipedia.org/wiki/Normseite) á 250 Worten, Stand Mai 2024)*

Alle Modelle analysieren und schreiben unterschiedlich und sind alle einen Versuch wert. Die Claude-Modelle werden von [Anthropic](https://www.anthropic.com/) betrieben, die GPT-Modelle von [OpenAI](https://openai.com/), das Mistral-Modell von [Mistral](https://mistral.ai/).<br>


### Wie funktioniert die Bewertung der Verständlichkeit?
Wir haben einen Algorithmus entwickelt, der die Verständlichkeit von Texten auf einer Skala von 0 bis 20 Punkten bewertet. Dieser Algorithmus basiert auf drei Textmerkmalen: Dem [Lesbarkeitsindex RIX](https://www.jstor.org/stable/40031755), der Häufigkeit von einfachen, verständlichen, viel genutzten Worten, sowie Satzlängen. Wir haben dies systematisch ermittelt, indem wir geschaut haben, welche Merkmale am aussagekräftigsten für Verwaltungs- und Rechtssprache und deren Vereinfachung sind.

Die Bewertung kannst du so interpretieren:

- **Sehr schwer verständliche Texte** wie Rechts- oder Verwaltungstexte haben meist Werte von **0 bis 13 Punkten**.
- **Durchschnittlich verständliche Texte** wie Nachrichtentexte, Wikipediaartikel oder Bücher haben meist Werte von **13 bis 16 Punkten**.
- **Gut verständliche Texte im Bereich Einfacher Sprache und Leichter Sprache** haben meist Werte von **16 bis 20 Punkten**.

Wir zeigen dir zusätzlich eine grobe Schätzung des Sprachniveaus gemäss [CEFR (Common European Framework of Reference for Languages)](https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions) von A1 bis C2 an.  

### Image ###

Die Bewertung ist bei weitem nicht perfekt, aber sie ist ein guter erster Anhaltspunkt und hat sich bei unseren Praxistests bewährt.


### Feedback
Wir sind für Rückmeldungen und Anregungen jeglicher Art dankbar und nehmen diese jederzeit gern [per Mail entgegen](mailto:datashop@statistik.zh.ch).


## Versionsverlauf
- **v0.1** - 1.06.2024 - *Erste Open Source-Version der App auf Basis des bisherigen Pilotprojekts.*