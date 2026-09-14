from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected RP5 patch target not found in {path}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Destination Sol includes the controller API in the engine, but Android also
# needs the Android controller manager implementation at runtime.
replace_once(
    "android/build.gradle",
    '    implementation "com.badlogicgames.gdx:gdx-backend-android:$gdxVersion"\n',
    '    implementation "com.badlogicgames.gdx:gdx-backend-android:$gdxVersion"\n'
    '    implementation "com.badlogicgames.gdx-controllers:gdx-controllers-android:$gdxControllersVersion"\n',
)

# Upstream deliberately forces mobile builds to the touch/keyboard mode.
# On the RP5 build, default new installs to the existing controller mode while
# still honoring a saved selection from settings.ini.
replace_once(
    "engine/src/main/java/org/destinationsol/GameOptions.java",
    '        controlType = mobile ? ControlType.KEYBOARD : Enums.getIfPresent(ControlType.class,  reader.getString("controlType", "MIXED")).or(ControlType.MIXED);\n',
    '        String defaultControlType = mobile ? "CONTROLLER" : "MIXED";\n'
    '        controlType = Enums.getIfPresent(ControlType.class, reader.getString("controlType", defaultControlType))\n'
    '                .or(mobile ? ControlType.CONTROLLER : ControlType.MIXED);\n',
)

# Upstream hides both input-mode selection and controller remapping on Android.
# Keep them visible on RP5 so a user can fall back to touch/keyboard mode or
# remap unusual Android controller axis/button IDs without rebuilding the APK.
replace_once(
    "engine/src/main/java/org/destinationsol/ui/nui/screens/mainMenu/OptionsScreen.java",
    '''        KeyActivatedButton controlTypeButton = find("controlTypeButton", KeyActivatedButton.class);\n        if (solApplication.isMobile()) {\n            menuButtonsLayout.removeWidget(controlTypeButton);\n        } else {\n            controlTypeButton.setText("Input: " + solApplication.getOptions().controlType.getHumanName());\n            controlTypeButton.subscribe(button -> {\n                solApplication.getOptions().advanceControlType(false);\n                controlTypeButton.setText("Input: " + solApplication.getOptions().controlType.getHumanName());\n            });\n        }\n''',
    '''        KeyActivatedButton controlTypeButton = find("controlTypeButton", KeyActivatedButton.class);\n        controlTypeButton.setText("Input: " + solApplication.getOptions().controlType.getHumanName());\n        controlTypeButton.subscribe(button -> {\n            // Use the desktop cycle here so Controller remains selectable on Android.\n            solApplication.getOptions().advanceControlType(false);\n            controlTypeButton.setText("Input: " + solApplication.getOptions().controlType.getHumanName());\n        });\n''',
)

replace_once(
    "engine/src/main/java/org/destinationsol/ui/nui/screens/mainMenu/OptionsScreen.java",
    '''        KeyActivatedButton controlsButton = find("controlsButton", KeyActivatedButton.class);\n        if (solApplication.isMobile()) {\n            menuButtonsLayout.removeWidget(controlsButton);\n        } else {\n            controlsButton.subscribe(button -> {\n                InputMapScreen inputMapScreen = solApplication.getMenuScreens().inputMapScreen;\n                switch (solApplication.getOptions().controlType) {\n                    case KEYBOARD:\n                        inputMapScreen.setOperations(inputMapScreen.getInputMapKeyboardScreen());\n                        break;\n                    case MIXED:\n                        inputMapScreen.setOperations(inputMapScreen.getInputMapMixedScreen());\n                        break;\n                    case CONTROLLER:\n                        inputMapScreen.setOperations(inputMapScreen.getInputMapControllerScreen());\n                }\n                nuiManager.setScreen(inputMapScreen);\n            });\n        }\n''',
    '''        KeyActivatedButton controlsButton = find("controlsButton", KeyActivatedButton.class);\n        controlsButton.subscribe(button -> {\n            InputMapScreen inputMapScreen = solApplication.getMenuScreens().inputMapScreen;\n            switch (solApplication.getOptions().controlType) {\n                case KEYBOARD:\n                    inputMapScreen.setOperations(inputMapScreen.getInputMapKeyboardScreen());\n                    break;\n                case MIXED:\n                    inputMapScreen.setOperations(inputMapScreen.getInputMapMixedScreen());\n                    break;\n                case CONTROLLER:\n                    inputMapScreen.setOperations(inputMapScreen.getInputMapControllerScreen());\n            }\n            nuiManager.setScreen(inputMapScreen);\n        });\n''',
)

print("Applied Destination Sol RP5 controller patches")
