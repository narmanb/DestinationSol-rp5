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

# The stock Android controller manager consumes gamepad KeyEvents after turning
# them into gdx-controller events. Destination Sol still uses its normal key
# input path for map/inventory/talk/shop/etc. Keep the controller event, but let
# the same Android key event continue through LibGDX as well.
rp5_controller = Path(
    "android/src/com/miloshpetrov/sol2/android/Rp5AndroidControllers.java"
)
rp5_controller.write_text(
    '''package com.miloshpetrov.sol2.android;

import android.view.KeyEvent;
import android.view.View;

import com.badlogic.gdx.controllers.android.AndroidControllers;

/**
 * Android controller manager for handhelds such as the Retroid Pocket 5.
 *
 * The upstream manager consumes gamepad key events after emitting controller
 * events. Destination Sol's menu/interface actions are still key-driven, so we
 * preserve the controller event and return false to allow the normal LibGDX
 * Android input backend to process the same key too.
 */
public class Rp5AndroidControllers extends AndroidControllers {
    @Override
    public boolean onKey(View view, int keyCode, KeyEvent keyEvent) {
        super.onKey(view, keyCode, keyEvent);
        return false;
    }
}
''',
    encoding="utf-8",
)

replace_once(
    "android/src/com/miloshpetrov/sol2/android/SolAndroid.java",
    '        AndroidApplicationConfiguration config = new AndroidApplicationConfiguration();\n\n        try {\n',
    '        AndroidApplicationConfiguration config = new AndroidApplicationConfiguration();\n'
    '        com.badlogic.gdx.controllers.Controllers.preferredManager = Rp5AndroidControllers.class.getName();\n\n'
    '        try {\n',
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

# The upstream controller remap screen intentionally accepts controller input
# only for the first seven ship actions. For every later action a gamepad event
# closes the capture UI without saving anything. Let those key-driven actions
# capture Android gamepad button keycodes too.
replace_once(
    "engine/src/main/java/org/destinationsol/menu/InputMapControllerScreen.java",
    '''            if (selectedIndex >= controllerItems) {\n                return "Enter New Key";\n            } else {\n                return "Enter New Controller Input";\n            }\n        } else {\n            return "Only ship controls can use a\\ncontroller in this version.\\n\\nMenu controls need to use\\nthe keyboard.";\n        }\n''',
    '''            if (selectedIndex >= controllerItems) {\n                return "Enter New Key or Controller Button";\n            } else {\n                return "Enter New Controller Input";\n            }\n        } else {\n            return "Ship controls accept axes or buttons.\\n\\nMenu/interface controls accept\\nkeyboard keys or controller buttons.";\n        }\n''',
)

replace_once(
    "engine/src/main/java/org/destinationsol/menu/InputMapControllerScreen.java",
    '''                    if (selectedIndex >= controllerItems) {\n                        removeDuplicateKeys(keycode);\n                        InputConfigItem item = itemsList.get(selectedIndex);\n                        item.setInputKey(Input.Keys.toString(keycode));\n                        itemsList.set(selectedIndex, item);\n                    }\n\n                    Gdx.input.setInputProcessor(inputProcessor);\n                    Controllers.clearListeners();\n\n                    isEnterNewKey = false;\n                    return true; // return true to indicate the event was handled\n''',
    '''                    if (selectedIndex >= controllerItems) {\n                        removeDuplicateKeys(keycode);\n                        InputConfigItem item = itemsList.get(selectedIndex);\n                        item.setIsAxis(false);\n                        item.setControllerInput(keycode);\n                        item.setInputKey(Input.Keys.toString(keycode));\n                        itemsList.set(selectedIndex, item);\n\n                        Gdx.input.setInputProcessor(inputProcessor);\n                        Controllers.clearListeners();\n                        isEnterNewKey = false;\n                        return true;\n                    }\n\n                    // Ship controls are captured by the controller listener below.\n                    // Do not let the Android key copy of the same button cancel capture.\n                    return false;\n''',
)

replace_once(
    "engine/src/main/java/org/destinationsol/menu/InputMapControllerScreen.java",
    '''                    if (selectedIndex < controllerItems) {\n                        removeDuplicateButtons(buttonIndex);\n                        InputConfigItem item = itemsList.get(selectedIndex);\n                        item.setIsAxis(false);\n                        item.setControllerInput(buttonIndex);\n                        item.setInputKey("Button: " + buttonIndex);\n                        itemsList.set(selectedIndex, item);\n                    }\n\n                    Gdx.input.setInputProcessor(inputProcessor);\n                    Controllers.clearListeners();\n\n                    isEnterNewKey = false;\n                    return true; // return true to indicate the event was handled\n''',
    '''                    if (selectedIndex < controllerItems) {\n                        removeDuplicateButtons(buttonIndex);\n                        InputConfigItem item = itemsList.get(selectedIndex);\n                        item.setIsAxis(false);\n                        item.setControllerInput(buttonIndex);\n                        item.setInputKey("Button: " + buttonIndex);\n                        itemsList.set(selectedIndex, item);\n                    } else {\n                        // Android controller button IDs are Android/LibGDX keycodes\n                        // (BUTTON_A, BUTTON_B, START, L1, etc.), so the existing\n                        // key-driven actions can store and use them directly.\n                        removeDuplicateButtons(buttonIndex);\n                        removeDuplicateKeys(buttonIndex);\n                        InputConfigItem item = itemsList.get(selectedIndex);\n                        item.setIsAxis(false);\n                        item.setControllerInput(buttonIndex);\n                        item.setInputKey(Input.Keys.toString(buttonIndex));\n                        itemsList.set(selectedIndex, item);\n                    }\n\n                    Gdx.input.setInputProcessor(inputProcessor);\n                    Controllers.clearListeners();\n\n                    isEnterNewKey = false;\n                    return true; // return true to indicate the event was handled\n''',
)

replace_once(
    "engine/src/main/java/org/destinationsol/menu/InputMapControllerScreen.java",
    '''                    if (value > 0.5f || value < -0.5f) {\n                        if (selectedIndex < controllerItems) {\n                            InputConfigItem item = itemsList.get(selectedIndex);\n                            item.setIsAxis(true);\n                            item.setControllerInput(axisIndex);\n                            item.setInputKey("Axis: " + axisIndex);\n                            itemsList.set(selectedIndex, item);\n                        }\n\n                        Gdx.input.setInputProcessor(inputProcessor);\n                        Controllers.clearListeners();\n\n                        isEnterNewKey = false;\n\n                    }\n''',
    '''                    if ((value > 0.5f || value < -0.5f) && selectedIndex < controllerItems) {\n                        InputConfigItem item = itemsList.get(selectedIndex);\n                        item.setIsAxis(true);\n                        item.setControllerInput(axisIndex);\n                        item.setInputKey("Axis: " + axisIndex);\n                        itemsList.set(selectedIndex, item);\n\n                        Gdx.input.setInputProcessor(inputProcessor);\n                        Controllers.clearListeners();\n                        isEnterNewKey = false;\n                    }\n''',
)

# Upstream forgot to handle the controllerDown boolean for button-based input.
# D-pad/button Down could be assigned in the menu but would never move the ship.
replace_once(
    "engine/src/main/java/org/destinationsol/game/screens/ShipControllerControl.java",
    '''                } else if (buttonIndex == gameOptions.getControllerButtonUp()) {\n                    controllerUp = true;\n                }\n\n                return true;\n''',
    '''                } else if (buttonIndex == gameOptions.getControllerButtonUp()) {\n                    controllerUp = true;\n                } else if (buttonIndex == gameOptions.getControllerButtonDown()) {\n                    controllerDown = true;\n                }\n\n                return true;\n''',
)

replace_once(
    "engine/src/main/java/org/destinationsol/game/screens/ShipControllerControl.java",
    '''                } else if (buttonIndex == gameOptions.getControllerButtonUp()) {\n                    controllerUp = false;\n                }\n\n                return true;\n''',
    '''                } else if (buttonIndex == gameOptions.getControllerButtonUp()) {\n                    controllerUp = false;\n                } else if (buttonIndex == gameOptions.getControllerButtonDown()) {\n                    controllerDown = false;\n                }\n\n                return true;\n''',
)

print("Applied Destination Sol RP5 controller patches")
