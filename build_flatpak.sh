#!/bin/bash

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo "flatpak-builder not found. Please install it first."
    exit 1
fi

# Add Flathub repository if not already added
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install required SDK and Platform
flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08

# Build the Flatpak package
flatpak-builder --force-clean build-dir com.go2engle.etsytrackr.yml

# Create a repository
flatpak-builder --repo=repo --force-clean build-dir com.go2engle.etsytrackr.yml

# Build a single-file bundle
flatpak build-bundle repo etsytrackr.flatpak com.go2engle.etsytrackr
