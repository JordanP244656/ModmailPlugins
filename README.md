# Modmail Analytics Plugin

Simple analytics plugin for Modmail that tracks ticket activity and
gives a quick overview of how things are going.

------------------------------------------------------------------------

**Features**

-   Tracks how many tickets are opened
-   Tracks how many tickets are closed
-   Calculates average time a ticket stays open
-   Weekly and monthly reports
-   CSV export (works with Excel / Google Sheets)
-   No setup required

------------------------------------------------------------------------

**Installation**
```
?plugin add JordanP244656/ModmailPlugins/analytics@main
```
------------------------------------------------------------------------

**Commands**

```.analytics```
Shows usage.

```.analytics weekly```
Shows stats from the last 7 days.

```.analytics monthly```
Shows stats from the last 30 days.

```.analytics export```
Exports the last 7 days as a CSV file.

------------------------------------------------------------------------

**How it works**

The plugin listens for ticket events.

-   When a ticket opens, it stores the timestamp
-   When a ticket closes, it calculates how long it was open

Everything is grouped by category automatically.

------------------------------------------------------------------------

**Example**

Discord output:

Support Opened: 42 Closed: 38 Avg Time: 12m 32s

CSV output:

Category,Opened,Closed,Average Time Support,42,38,12m 32s
Moderation,27,25,8m 10s

<img width="214" height="134" alt="image" src="https://github.com/user-attachments/assets/c278b8db-c910-4de9-8297-309b36e2dc02" />   
<img width="261" height="73" alt="image" src="https://github.com/user-attachments/assets/b3468ac0-5d62-41ef-b3fe-e6653c312539" />

------------------------------------------------------------------------

**Plans**

-   Automatic weekly reports
-   Configurable report channel
-   Add more compatibility so you can set your own timestamps!
-   Saves on CSV with Accurate Period of Data & Exportation Time & Date
-   Outputs with the Accurate Period of Data (meaning shows you what date)
-   Get this on the registry!
-   Create more plugins!
