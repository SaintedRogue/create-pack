# Setting up a PC to play Ahrendt Engineering

This takes about 15 minutes per PC the first time. After that the game updates itself every
time it's launched, so you never repeat these steps.

**You need:** the kid's Microsoft account login, and the PC on the home network (the server is
only reachable at home).

---

## 1. Make sure the account owns Minecraft: Java Edition

This modpack is **Java Edition only**. Bedrock (Xbox, Switch, tablet and phone versions) can't
join it.

1. Install the official **Minecraft Launcher** from <https://www.minecraft.net/download> and sign in
   with the kid's Microsoft account.
2. If it offers **"Minecraft: Java Edition" → Play**, you're set. Close the launcher.
   If it only offers to buy Java Edition, the account doesn't own it. PC copies bought since 2022
   ("Java & Bedrock Edition for PC") include it; console and tablet copies don't.
3. Note the **Java username** shown in the launcher (top left). It is *not* the Xbox gamertag.
   Send it to Mike so it can go on the server's whitelist.

## 2. Allow multiplayer on a child account

Microsoft blocks multiplayer on child accounts by default, which shows up as
*"Multiplayer is disabled. Please check your Microsoft account settings."*

1. On the parent's account, go to <https://account.xbox.com/Settings> and pick the child, or use
   the **Xbox Family Settings** app.
2. Set **"You can join multiplayer games"** to **Allow**.

## 3. Install Prism Launcher

1. Download it from <https://prismlauncher.org/download> and install with the defaults.
2. Open it. Click **Accounts** (top right) → **Manage Accounts** → **Add Microsoft**, and sign in
   with the kid's account.
3. Prism downloads the right Java automatically when it needs it. If it asks, say yes.

## 4. Import the modpack

1. In Prism click **Add Instance** → **Import**.
2. Paste this link and click **OK**:
   `https://github.com/SaintedRogue/create-pack/releases/latest/download/Ahrendt-Engineering-public.mrpack`
3. Wait for the new **Ahrendt Engineering** instance to appear.

## 5. Turn on automatic updates (important)

This step keeps the PC matched to the server. Without it the game won't be able to join after
the next server update. It also downloads three mods (the FTB mods) that the import file can't
include, so the **first** launch fails to connect without it.

1. Right-click the instance → **Edit** → **Settings** → **Custom commands**.
2. Tick **Custom commands**, and in **Pre-launch command** paste exactly:
   ```
   "$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/SaintedRogue/create-pack/release/pack/pack.toml
   ```
3. Still in **Settings**, open **Java** → tick **Memory** → set **Maximum memory** to **6144 MiB**
   (or **4096** on a PC with 8 GB of RAM or less).
4. Close the window.

## 6. First launch and joining

1. Double-click the instance. A small **"Updating"** window appears and downloads mods. That's
   the auto-update doing its job. The first time takes a few minutes; afterwards it's a few seconds.
2. When the title screen appears: **Multiplayer** → **Add Server**:
   - Server Name: `Ahrendt Engineering`
   - Server Address: `10.0.0.180:25570`
3. Join. If it says **"You are not white-listed on this server"**, send Mike the Java username
   from step 1.

## 7. Optional: shaders and Fresh Animations

The pack comes with nicer visuals already downloaded, but **switched off**, so each PC chooses.
Both settings are saved per PC, and pack updates never change them.

- **Shaders** (realistic lighting, shadows, water and sky): **Options → Video Settings → Shader Packs…**
  → click **ComplementaryReimagined** → **Done**. To turn them off again, pick **(off)** in the same list.
  These work well on the RTX 2080, 5060 and 4090 at 1080p. On the 2080, lower the shader's quality
  profile if it stutters (Shader Packs → **Shader Pack Settings** → Profile → **Medium**).
  Create's moving machines keep their fast rendering with shaders on, thanks to the **Colorwheel** mod.
- **Fresh Animations** (mobs blink, look around and move naturally): **Options → Resource Packs…** →
  hover **Fresh Animations** in the left list → click the **▶** arrow so it moves to the right → **Done**.
  It's light enough to leave on everywhere.

---

### If something goes wrong

| What you see | Fix |
|---|---|
| "Multiplayer is disabled…" | Step 2 (child account setting). |
| "Mod rejections" / "missing mods" when joining | The auto-update didn't run. Check step 5, then relaunch. |
| The Updating window shows an error | Usually no internet or GitHub is down. Close it and launch again later. |
| "Connection refused" / can't find the server | You're not on the home network, or the server is restarting (it restarts nightly around 3:30 AM and again around 4:30 AM, for a few minutes each). |
| Game is slow | Turn shaders off (step 7), or in Video Settings lower Render Distance to 8. |
