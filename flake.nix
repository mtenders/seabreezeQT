{
  description = "GUI for Ocean Optics spectrometers";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonEnv = pkgs.python3.withPackages (ps: [
          ps.numpy
          ps.seabreeze
          ps.pyqt5
          ps.pyqtgraph
        ]);
      in
      {
        devShell = pkgs.mkShell {
          QT_QPA_PLATFORM_PLUGIN_PATH = "${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins";
          packages = [
            pythonEnv
          ];
        };
      }
    );
}
