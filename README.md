# Forellen Slussfors – direktbokningssida

Statisk sida (engelska), en enda `index.html` + `images/`. Kräver ingen server-kod.

```
index.html     hela sidan (CSS + JS inbyggt)
availability.json  upptagna datum, skrivs av tools/update_availability.py
tools/update_availability.py  hämtar iCal från Airbnb + Booking (bara datum)
private/       ical_sources.json med de HEMLIGA iCal-länkarna, ladda ALDRIG upp
images/        27 foton från Airbnb-annonsen, 1600 px, EXIF/GPS borttaget
_original/     samma foton i 1920 px från Airbnb (ladda inte upp, bara arkiv)
```

## Fyll i innan publicering
Allt ändras i blocket `window.FORELLEN` högst upp i `index.html`:

- `bookingEmail` – adressen förfrågningarna går till (jonasekman72@gmail.com).
- `formspreeId` – "mdegpnkw" (formspree.io, Jonas konto). Förfrågan postas direkt till Formspree som
  mejlar jonasekman72@gmail.com; svara på mejlet så går svaret till gästen. Tomt = mailto.
- `airbnbNightly`, `airbnbExtraGuest` – Airbnbs listpriser 2027 (1 100/1 150 kr för 2 gäster,
  +100 kr per extra gäst). `directDiscount: 0.05` ger direktpris 5 % under Airbnb
  (avrundat till 5 kr: 1 045/1 095 kr, +95 kr). Sätt 0 för samma pris som Airbnb.
- `weeklyDiscount`, `minNights`, `linenPerPerson` – vecka −15 %, minst 3 nätter, lakan 200 kr/person.
  Prislistan och priskalkylatorn räknas fram ur dessa automatiskt.

## Betalning (PayPal)
Sidan lovar en PayPal-betalningsbegäran där gästen kan betala med kort utan PayPal-konto.
Kontrollera i PayPal: Kontoinställningar → Webbplatsbetalningar → Webbplatsinställningar →
"PayPal-konto valfritt" = På. Testa sedan med en faktura till en adress utan PayPal-konto.

## Kalendern
```bash
cd ~/forellen-slussfors && python3 tools/update_availability.py
```
Hämtar båda iCal-flödena, slår ihop upptagna nätter och skriver `availability.json`.
Om något flöde fallerar lämnas den gamla filen orörd (visar hellre upptaget än fel ledigt).
Måste köras regelbundet (t.ex. var 30:e minut) där sidan ligger, och kalendern på
sidan blir aldrig mer aktuell än senaste körningen. Gäster bekräftas ändå manuellt.

## Innehåll som bygger på källor (nov 2026)
- Fiskearter, fiskekortspriser och rödingodlingen: iFiske, Slussfors KFO (100/250/700 kr) och Kirjesåns KFO (150/400/700 kr, Kirjesån + Nedre Lumnien).
- Husbeskrivning, in-/utcheckning 14/12, betyg 4.74 och recensionscitat: Airbnb-annonsen.
- Koordinater: hus från Airbnb-kartan, sjöar/båtramp från OpenStreetMap.
- Säsongsstaplarna per art är en grov egen tumregel, inte iFiskes regler.

## Förhandsvisa lokalt
```bash
cd ~/forellen-slussfors && python3 -m http.server 8093
```
