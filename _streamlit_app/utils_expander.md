Dieser Prototyp ist Teil eines Projekts vom Amt für Statistik und Daten, Kanton Zürich. Mit diesem Projekt möchten wir öffentliche Organisationen dabei unterstützen, ihre Kommunikation noch verständlicher aufzubereiten.

## Wichtig

- **:red[Nutze die App nur für öffentliche, nicht sensible Daten.]**
- **:red[Die App liefert lediglich einen Entwurf. Überprüfe das Ergebnis immer – idealerweise mit Menschen aus dem Zielpublikum – und passe es an, wenn nötig.]**

## Was macht diese App?

**Diese App übersetzt einen von dir eingegebenen Text in einen Entwurf für Einfache Sprache oder Leichte Sprache.**

Die App ergänzt deinen Text um Anweisungen und schickt ihn über OpenRouter an ein grosses Sprachmodell (LLM, Large Language Model) eines Modellanbieters. Diese Sprachmodelle sind in der Lage, Texte nach Anweisungen umzuformulieren und dabei zu vereinfachen.

Du kannst die Texte nach den Regeln für Einfache Sprache oder Leichte Sprache übersetzen.

- **Leichte Sprache** ist eine vereinfachte Form der deutschen Sprache, die nach bestimmten Regeln gestaltet wird. Leichte Sprache hilft u.a. Menschen mit Lernschwierigkeiten oder geringen Deutschkenntnissen.
- **Einfache Sprache** ist eine vereinfachte Version von Alltagssprache. Diese zielt darauf, Texte generell für ein breiteres Publikum verständlicher zu machen.

In der Grundeinstellung übersetzt die App in Einfache Sprache. Wenn du den Schalter «Leichte Sprache» klickst, weist du die App an, einen Entwurf in **Leichter Sprache** zu schreiben. Wenn Leichte Sprache aktiviert ist, kannst du zusätzlich wählen, ob das Modell alle Informationen übernehmen oder versuchen soll, sinnvoll zu verdichten. Die Verdichtung ist standardmässig aktiviert.

**Die App liefert einen Entwurf, der Fehler enthalten kann. Überprüfe den Text und passe ihn bei Bedarf an.** Insbesondere bei Leichter Sprache ist die Überprüfung der Ergebnisse durch Prüferinnen und Prüfer aus dem Zielpublikum essentiell.

### Wie funktioniert die Bewertung der Verständlichkeit?

Die App verwendet das externe Paket [ZIX](https://github.com/machinelearningZH/zix_understandability-index). Es bewertet Texte auf einer Skala von -10 bis 10 anhand von Satzlängen, dem Lesbarkeitsindex RIX, häufigen Wörtern und dem Anteil an Wörtern aus den Vokabularen A1, A2 und B1. Die Bewertung prüft weder die sachliche Richtigkeit noch die Einhaltung aller Sprachregeln.

In der aktuellen Konfiguration ordnet die App den ungerundeten Wert so ein:

- **Unter -2:** schwer verständlich.
- **Von -2 bis unter 0:** nur mässig verständlich.
- **Ab 0:** gut verständlich.

Die angezeigte Zahl ist gerundet. Beim Vereinfachen siehst du den Wert des Ergebnisses und die Veränderung gegenüber dem Ausgangstext. Beim Analysieren siehst du den Wert des Ausgangstexts.

Mit «One-Klick» schickst du deinen Text gleichzeitig an alle konfigurierten Modelle. Erfolgreiche Ergebnisse enthalten jeweils eine Bewertung. Fehlgeschlagene Modelle werden aufgeführt, sofern mindestens ein Modell ein Ergebnis liefert. Du kannst Ergebnisse und Ausgangstext als Word-Dokument herunterladen.

Wir zeigen dir zusätzlich eine **grobe** Schätzung des Sprachniveaus gemäss [CEFR (Common European Framework of Reference for Languages)](https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions) von A1 bis C2 an.

ADD_IMAGE_HERE

Die Bewertung und die Illustration dienen als Orientierung. Trainingsdaten und Nachweise zur Kalibrierung sind in diesem Repository nicht enthalten. Ein positiver Wert bestätigt nicht, dass ein Text alle Anforderungen an Einfache oder Leichte Sprache erfüllt.

### Feedback

Wir sind für Rückmeldungen und Anregungen jeglicher Art dankbar und nehmen diese jederzeit gern [per Mail entgegen](mailto:datashop@statistik.zh.ch).
