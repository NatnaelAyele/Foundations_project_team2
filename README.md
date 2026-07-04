# FreshLink Admin Operations Workspace

Admin dashboard frontend for **FreshLink — Post-Harvest Logistics Coordination Platform**, a university group project supporting coordination between admins, smallholder tomato farmers, cold hub operators, and truck providers in Kamonyi District, Rwanda.

This deliverable covers the **admin dashboard only**. The landing page and login page were built by a teammate and are not part of this task.

## Pages built

| File | Purpose |
|---|---|
| `admin/admin-dashboard.html` | Admin Operations Workspace — welcome section, today's coordination focus, summary cards, and recent farmer/forecast tables |
| `admin/register-farmer.html` | Form for registering a new farmer (personal information + farm information) |
| `admin/view-farmers.html` | Searchable table of registered farmers |
| `admin/forecast.html` | Form for submitting a new harvest forecast |
| `admin/view-forecasts.html` | Searchable table of harvest forecasts |
| `admin/reports.html` | Coordination reports — monthly overview cards, forecast transport/storage split, farmers by sector, and forecast volume by month |

`static/css/admin.css` holds all shared styling and `static/js/admin.js` holds all shared behavior (nav dropdowns, form validation, success messages, table search, logout confirmation), so every page loads the same two files. `static/images/harvest-tomatoes.jpg` is the hero photo on the workspace page.

## Structure

```
frontend/
├── admin/
│   ├── admin-dashboard.html
│   ├── register-farmer.html
│   ├── view-farmers.html
│   ├── forecast.html
│   ├── view-forecasts.html
│   └── reports.html
├── static/
│   ├── css/admin.css
│   ├── js/admin.js
│   └── images/harvest-tomatoes.jpg
└── README.md
```

## Not included

- `index.html`, `login.html`, `landing.html` — already built by another teammate. This dashboard assumes the admin has already logged in. The Logout link currently points at `login.html`; update that path once the login page's real location in the merged repo is known.
- Any backend or database connection — all forms and tables use dummy data. Submitting a form shows a success message via JavaScript but does not persist anything.

## How to run

No build step or server is required.

1. Open `admin/admin-dashboard.html` directly in a browser, **or**
2. Serve the `frontend/` folder with any static server, e.g.:
   ```
   npx serve frontend
   ```
   then navigate to `admin/admin-dashboard.html` at the printed local URL.

## Design notes

- Top navigation bar with hover dropdowns for **Farmers** and **Harvest Forecast**, matching the landing page's top-nav layout instead of a sidebar.
- Color palette, typography (Inter), card style, and spacing follow the FreshLink landing page identity exactly as specified in the design brief.
- Dummy data (farmer names, villages, sectors, quantities) is illustrative of Kamonyi District and is meant to make the interface feel populated for report screenshots, not to represent real farmers.
