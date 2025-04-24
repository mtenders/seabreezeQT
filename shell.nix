{ pkgs ? import <nixpkgs> { } }:
with pkgs;
let
  pythonEnv =
    python38.withPackages (ps: [ ps.numpy ps.seabreeze ps.pyqt5 ps.pyqtgraph ]);
in mkShell {
  buildInputs = [ pythonEnv ];

  # Normally set by the wrapper, but we can't use it in nix-shell (?).
  QT_QPA_PLATFORM_PLUGIN_PATH =
    "${qt5.qtbase.bin}/lib/qt-${qt5.qtbase.version}/plugins";
}

