# Plover Touch Tablets Plugin

This Plover plugin enables seamless integration between Plover and touch-based steno keyboard applications running on tablets. It establishes a secure WebSocket connection, allowing your tablet to function as a steno machine for Plover.

## Compatibility

This plugin is designed to be compatible with the **[Touch Steno Keyboard](https://github.com/CosmicDNA/touch-steno-keyboard)** application and the **[Plover Websocket Relay](https://github.com/CosmicDNA/plover-websocket-relay)**.

## Features

- **Easy Pairing**: Generates a QR code within Plover for quick connection setup.
- **Secure Connection**: Uses encryption to ensure secure communication between the tablet and Plover.
- **Bi-directional Communication**: Supports sending steno strokes to Plover and receiving dictionary lookups/translations back on the tablet.

## Installation

1. Open Plover.
2. Install `plover-touch-tablets` plugin via either plover_console CLI or plugin manager.
3. Restart Plover.

## Usage

1. Open Plover.
2. Go to **Tools** > **Tablet QR**.
3. A window will appear displaying a QR code.
4. Open the Touch Steno Keyboard application on your tablet.
5. Use the application to scan the QR code displayed on your computer screen.
6. Once connected, strokes entered on the tablet will be processed by Plover.

## Powered by
![Python](https://img.shields.io/badge/Python-repo?logo=python&color=black&style=for-the-badge)
![Plover](https://img.shields.io/badge/Plover-repo?logo=plover&color=black&style=for-the-badge)
