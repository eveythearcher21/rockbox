# 2017 Volkswagen Tiguan: direct Y1 projection investigation

Requested layout: Recently Played, Playlists, Albums, Songs, Artists and Search (six entries), with sorting reachable away from the nonworking right-hand screen margin.

The user has no Android phone and requests direct Y1-to-car support. **This release does not implement or claim that connection.**

The repository builds Rockbox as an app on the Y1's existing Android platform (SDK 19). It has no phone-side Android Auto projection transport, CarPlay projection stack, car-facing media browser service, or USB gadget driver implementation. Changing Rockbox's theme and menus does not install those components. OpenAuto/AASDK projects implement the receiving/head-unit side; they do not by themselves turn the Y1 into an Android Auto phone. USB mass-storage playback or Bluetooth audio can be useful if the car supports them, but neither supplies the requested custom Rockbox interface.

A direct implementation would be a separate platform/projection project requiring:

1. Identification of the actual Tiguan App-Connect/MIB unit and enabled connection modes (model/firmware from its System Information screen).
2. The Y1's actual Android build, kernel source/configuration, USB gadget/accessory capabilities, and a recoverable development device. Android Auto's currently supported phone requirements exceed this old Android base; installing the current phone app is not a supported shortcut.
3. A usable phone-side projection stack and compatible authentication/transport; video encoding at the unit's negotiated resolution, input routing, USB audio, metadata and browse/queue commands, and disconnect/reconnect handling.
4. Tests with the car, including USB negotiation, sound, controls, touch behavior, and reconnects. The right edge should not contain required actions in any layout we control. The host projection system may impose its own media templates and controls, so an exact 2×3 grid/top-center filter position cannot be guaranteed through normal Android Auto media integration.

The cloud environment has neither the player's platform/kernel sources nor either USB-connected device, so it cannot establish that this direct route is implementable on the stock Y1 or verify it. There is no tested direct-connection installation procedure to provide.

A separate compatible Android/CarPlay bridge box with its own supported projection stack is the hardware route that could avoid an Android phone. That adds another device and is not equivalent to direct stock-Y1 projection. Its compatibility with the actual Tiguan unit and ability to access the Y1's library would need verification before selecting or writing integration software. No hardware purchase is assumed or required by the Y1 customization.

## Reported head unit and next check

The owner supplied: part/device identifier `5C0D352008`, Hardware `H30`, Software `0357`, media codec `3201.0.0.8`, in a 2017 Tiguan. MirrorLink availability is unconfirmed. These strings alone do not prove a usable projection mode or Y1 compatibility.

After installing this revision, open **System → Car connection check** on the Y1. Copy `.rockbox/carlink-diagnostics.txt` from the card and share it. The script reads platform/Android version, USB function/controller names, current USB mode, interface names, and selected kernel feature flags if exposed. It changes no USB configuration and records no device serial, account data, network addresses, Wi-Fi credentials, or tokens. Missing kernel configuration is reported as unknown, not as absent support. The System action uses the root execution mechanism already used by this fork's updater; availability must still be checked on the actual player.

Without the car/player connected to this environment, USB negotiation and projection cannot be tested here. This release supplies no projection server and no claim that plugging in the player will display Rockbox on App-Connect. If a compatible transport is established later, required controls must stay away from the damaged right screen margin.
