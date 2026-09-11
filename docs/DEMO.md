# Haven — Demo Video Script

**Target length:** 2:45
**Audience:** Hackathon judges (AWS Agents for Humans)
**Tone:** Warm, technical, emotionally compelling

---

## SCRIPT

### 0:00–0:20 — THE PROBLEM

**[Visual: B-roll of a real food bank — volunteers sorting cans, a director on the phone]**

> Every week, a food bank director named Rosa spends 30 hours on tasks that aren't feeding people.
>
> Reading donation texts. Matching volunteers to shifts. Answering the same questions. Filling reports.
>
> That's 30 hours of judgment-heavy repetitive work — for every food bank, in every city.
>
> What if an agent could do that invisible work?

---

### 0:20–0:45 — ENTER HAVEN

**[Visual: Architecture diagram animating in — agent nodes connecting]**

> Haven is an autonomous multi-agent system that runs the logistics of community aid.
>
> Five specialized agents — Donor, Volunteer, Recipient, Logistics, and Compliance — coordinated by an intelligent Supervisor.
>
> Built on the Strands Agents SDK, deployed on AWS Bedrock AgentCore.
>
> Let me show you a real day.

---

### 0:45–1:15 — DONATION OFFER VIA SMS

**[Visual: Phone screen showing SMS from "Green Farms Co."]**

> A restaurant texts: "Hey, we have 200 pounds of fresh vegetables. Can you pick them up today?"
>
> **[Visual: Haven dashboard — Donor Agent card lighting up]**
>
> The DonorAgent parses the offer instantly. It identifies the category — produce — checks cold-chain requirements: refrigerated transport needed, 8-hour window.
>
> **[Visual: Agent reasoning trace scrolling]**
>
> It accepts the donation, proposes a pickup window, and generates a tax receipt — all before a human even reads the text.
>
> **[Visual: Logistics Agent card activates]**
>
> LogisticsAgent picks it up. Optimizes a route: three pickups, 8.2 miles total. Generates a driver manifest with cold-chain instructions. Dispatches driver James Thompson.
>
> From text to truck in 12 seconds.

---

### 1:15–1:45 — VOLUNTEER MATCHING

**[Visual: Dashboard — Volunteers page]**

> Meanwhile, three shifts need filling for tomorrow.
>
> **[Visual: Volunteer Agent reasoning trace]**
>
> The VolunteerAgent scans 1,847 registered volunteers. It matches Maria Rodriguez to the morning sort shift — 98% match score based on her skills, availability, and perfect reliability record.
>
> **[Visual: SMS being sent to Maria]**
>
> Maria gets an SMS: "Hi Maria! A new shift is available at Downtown Pantry. Reply YES to confirm."
>
> She replies YES. Shift confirmed. Roster updated.
>
> No spreadsheet. No group text. No chasing people down.

---

### 1:45–2:15 — RECIPIENT IN SPANISH

**[Visual: Phone call incoming — Spanish caller ID]**

> Now the most important part. A mother calls. She speaks only Spanish.
>
> **[Visual: Recipient Agent — live translation in the dashboard]**
>
> She asks: "¿Tienen fórmula para bebé? Tengo un bebé de 3 meses."
>
> The RecipientAgent translates instantly. Searches nearby pantries. Finds one with baby formula in stock — Downtown Community Pantry, open until 4 PM, half a mile away.
>
> **[Visual: Bilingual response appearing]**
>
> It responds in Spanish with the address, hours, and a note: "No appointment needed. Walk in during operating hours."
>
> Life-changing information delivered in her language, in seconds.

---

### 2:15–2:30 — THE VISION

**[Visual: Dashboard overview — all 5 agents active, event feed flowing]**

> Today, Haven coordinates 247,000 meals across 23 pantries with 1,847 volunteers.
>
> Every agent action is logged in an immutable audit trail. USDA compliance reports generate automatically. Tax receipts are batched and sent.
>
> This isn't a chatbot. It's an operations layer — running in the background so humans can do human work.

---

### 2:30–2:45 — CTA

**[Visual: GitHub repo, live demo URL, project logo]**

> Haven is open source. Built with Strands Agents SDK on AWS.
>
> Every food bank deserves this infrastructure. Every volunteer deserves coordination this smooth. Every person asking for help deserves to be heard in their own language.
>
> **[Visual: haven-agent.org + GitHub URL]**
>
> Let's build the agent behind every helping hand.

---

## PRODUCTION NOTES

### Recording Setup
- Screen recording: OBS Studio (1080p60)
- Audio: External mic, quiet room
- B-roll: Stock footage of food banks (Pexels/Unsplash)
- Dashboard: Pre-populated with realistic demo data

### Key Demo Data Points
- 247,832 meals coordinated
- 1,847 active volunteers
- 3,421 donations this month
- 12-second average response time
- 8 languages supported

### Transitions
- Smooth zoom between phone screen and dashboard
- Agent cards "activate" with color pulse
- Reasoning traces appear with typing effect
- Stats count up when visible

### Music
- Ambient, warm, optimistic — no vocals
- Subtle beat during agent coordination section
- Swells slightly during the Spanish call resolution
