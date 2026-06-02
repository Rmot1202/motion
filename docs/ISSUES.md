# Issues Faced During Thermocouple Dashboard Development

## 1. MCC board had to be connected before launching the app

A major issue was that the application did not reliably recover if the MCC E-TC board was not already connected before startup. In practice, the user needed to have the board connected before running the application, otherwise the dashboard would fall back to simulation or fail to detect the device.

### Impact
This made the startup process less flexible because live hardware access depended on the device being available at launch time. If the board was not already present, the app could not reliably switch back to hardware mode later.

## 2. Refreshing the page reset preferences

Another issue was that refreshing the application caused saved preferences to reset. Dash supports client-side persistence for user controls, but it requires explicit configuration with persistence settings or stored browser state; otherwise, values can be lost on reload.

### Impact
The dashboard did not keep the same furnace settings, axis ranges, or sampling choices after a refresh. That meant users had to re-enter their preferences manually more often than expected.

### Why it happened
The app was not fully set up to persist all control values across reloads. Dash’s `dcc.Store` and component persistence features can preserve state in the browser, but they must be configured intentionally.

## 3. File saving worked locally but not over Wi‑Fi

A third issue was that file saving worked when testing locally, but when accessed through Wi‑Fi the file did not go to the user’s chosen directory. Instead, the browser sent it to the default recent downloads location or handled it according to the browser’s own download settings.

### Impact
This prevented the app from reliably controlling where the downloaded recording was stored on the user’s machine. The save behavior became dependent on the browser and the user’s download configuration rather than the app itself.

### Why it happened
Browser-based downloads are generally controlled by the browser, not by the server app. In Dash, download location is typically determined by browser settings such as “ask where to save each file” or the user’s default downloads folder.

## 4. Hardware detection and simulation fallback

The MCC device detection issue also created confusion between real readings and simulation mode. The board detection error showed up as `Specified Network board not detected`, which meant the app could not confirm the Ethernet board was available.

### Impact
When the hardware was not detected, the app used simulated data instead of live channel values. That helped keep the dashboard running, but it also made it harder to tell whether the real board was actually connected.

## 6. Overall lesson

The biggest lesson was that hardware-backed dashboards need clear boundaries between live device mode, simulation mode, and browser-controlled features like downloading and preference storage. The MCC board needed to be available at startup, preferences needed explicit persistence, and file save behavior depended on the browser environment rather than the local app logic.