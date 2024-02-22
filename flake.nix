{
  description = "FUSE-based euphoria.leet.nu client";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    flake-utils.url = "github:numtide/flake-utils";

    poetry2nix.url = "github:nix-community/poetry2nix";
    poetry2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        p2n = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };
      in
      {
        packages.default = p2n.mkPoetryApplication {
          projectDir = ./.;
          overrides = p2n.defaultPoetryOverrides.extend (self: super: {
            # https://github.com/nix-community/poetry2nix/blob/master/docs/edgecases.md#modulenotfounderror-no-module-named-packagename
            # https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/python-modules/fuse-python/default.nix
            fuse-python = super.fuse-python.overridePythonAttrs (old: {
              nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.pkg-config ];
              buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools pkgs.fuse ];
            });
          });
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.default ];
          packages = [ pkgs.poetry ];
        };
      });
}
