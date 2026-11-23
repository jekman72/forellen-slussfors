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

## Språk (EN · LV · LT)
Sidan finns på engelska, lettiska och litauiska. Språket väljs med EN/LV/LT i menyn,
med `?lang=lv`, via korta adresserna forellenslussfors.se/lv och /lt (för Facebook),
eller automatiskt efter telefonens språk.

- Texter i HTML är märkta med `data-i18n="nyckel"`. Engelska källan: `i18n/en.json`.
- Översättningar: `i18n/lv.json` och `i18n/lt.json` (nycklar `js.*` är texter som skapas i
  JavaScript, t.ex. prisrutan, kalendern och kartan).
- Ändrar du en engelsk text eller lägger till en ny:
  `python3 tools/tag_i18n.py` (märker nya element, uppdaterar en.json), översätt i lv/lt.json,
  sedan `python3 tools/build_i18n.py` (bygger `i18n/strings.js`). Saknade nycklar visas på engelska.
- Själva förfrågan som mejlas till oss är alltid på engelska.
- Översättningen är maskinnära, låt gärna en lettisk/litauisk gäst läsa igenom.

## Besöksstatistik
Cloudflare Web Analytics (gratis, inga cookies, ingen samtyckesruta). Konto: jonasekman72@gmail.com
på dash.cloudflare.com → Analytics → Web analytics → forellenslussfors.se. Skriptet ligger sist i
`index.html` (token är offentlig). Statistiken visas med några minuters fördröjning.

## Pi:n (EnergyPilot-Pi:n, jonas@energypilot) kör två jobb
Helt separat från EnergyPilot, i `~/forellen` (klon av repot) med hemligheterna i `~/forellen/private`.
- Var 30:e minut: `tools/pi_sync.sh` hämtar iCal; bara om bokade datum ändrats görs en tom commit
  som får GitHub att bygga om sidan (deploy-nyckel `~/.ssh/forellen_deploy`, skrivrätt bara till detta repo).
- 10:00: `tools/daily_stats.py --push` skickar gårdagens besök till ntfy-ämnet i `private/ntfy_topic`.
Loggar: `~/forellen/private/pi_sync.log` och `daily_stats.log`. Se `crontab -l` på Pi:n.
Stoppa: ta bort de två forellen-raderna med `crontab -e` och radera deploy-nyckeln i GitHub.
