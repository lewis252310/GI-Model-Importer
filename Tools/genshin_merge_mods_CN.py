# Author: SilentNightSound#7430
# Special Thanks:
#   Takoyaki#0697 (for demonstrating principle and creating the first proof of concept)
#   HazrateGolabi#1364 (for implementing the code to limit toggles to the on-screen character)

#   HummyR#8131, Modder4869#4818 (3.0+ Character Shader Fix)

#   !someone name has 63B long?#lewis252310 (Translatable version, CN translation ver)
# V3.0 of Mod Merger/Toggle Creator Script

# Merges multiple mods into one, which can be toggled in-game by pressing a key

# USAGE: Run this script in a folder which contains all the mods you want to merge
# So if you want to merge mods CharA, CharB, and CharC put all 3 folders in the same folder as this script and run it

# This script will automatically search through all subfolders to find mod ini files.
# It will not use .ini if that ini path/name contains "disabled"

# NOTE: This script will only function on mods generated using the 3dmigoto GIMI plugin

import os
import re
import argparse
import hashlib

import ctypes

from enum import Enum


def log(msg: str):
    print(len(msg))
    if "\n" in msg:
        print("Found \\n. Follow setted string.\n")
        print(msg)
    else:
        print("Not found \\n. Run auto string cutting.\n")
        print(msg)


class Message(Enum):
    ARG_DISCRIPTION = "從多個mod文件夾生成合併mod"
    ARG_HELP_ROOT = "用於創建mod的位置"
    ARG_HELP_STORE = "在完成後保留原始的 .ini 文件啟用狀態"
    ARG_HELP_ENABLE = ""
    ARG_HELP_NAME = ""
    ARG_HELP_KEY = ""
    ARG_HELP_COMPRESS = ""
    ARG_HELP_ACTIVE = ""
    ARG_HELP_REFLECTION = ""

    INFO_TITLE = "\x1b[7m\n某知名動漫遊戲模組合併/切換生成器腳本\x1b[0m\n"
    INFO_ACTIVE = "設置為僅交換當前（在屏幕上顯示的）角色"
    INFO_ENABLE = "重新啟用所有 .ini 文件"
    INFO_STORE_1 = "\n\x1b[33m警告：一旦此腳本完成，它將禁用被合併的 Mod 各自的 .ini 文件（為了讓最終版本在沒有衝突的情況下運作，這是必需的）"
    INFO_STORE_2 = "您可以使用 -s 選項來阻止此行為"
    INFO_STORE_3 = "此腳本還可以使用 -e 選項重新啟用當前文件夾及其所有子文件夾中的所有 mod，如果需要重新生成合併的 ini，請使用此選項\x1b[0m"
    INFO_COMPRESS = "\n警告2：-c/--compress 選項將使輸出變得更小，但從合併後的 mod 中檢索原始 mod 將變得困難。請確保有備份，並且請在確保一切正常後再使用此選項"
    INFO_INI_SEARCH = "\n搜索 .ini 文件中…"
    INFO_INI_FOUND = "\n找到："
    INFO_HOW_THIS_WORK_1 = "\n此腳本將按上述列出的順序進行合併（0 是 mod 開始的默認設置，並將循環 0,1,2,3,4,0,1...等等）"
    INFO_HOW_THIS_WORK_2 = "如果沒問題，請按回車繼續。如果有問題，請輸入您希望腳本合併 mod 的順序（例如：3 0 1 2）"
    INFO_HOW_THIS_WORK_3 = "如果輸入的順序數量小於總數量，腳本將只合併列出的順序。\n"
    INFO_TOGGLE_KEY = "\n請輸入用於切換 mod 的按鍵（也可以使用 -k 選項輸入，或在 .ini 文件中稍後設定）。按鍵必須是一個單獨的字母\n"
    INFO_INI_PARSING = "正在解析 .ini 文件…"
    INFO_CALUCUATING_OVR_RES_SECTION = "正在計算 Overrides 節和 Resources 節…"
    INFO_FIXXING_CHARACTER_SHADER = "角色著色器修復…"
    INFO_CREATING_CMD_SECTION = "正在建立 CommandList 節…"
    INFO_OUTPUT_RUNNING_RESULTS = "正在輸出運行結果…"
    INFO_CALER_DISABLE_EACH_INI = "清理並禁用 Mod 各自的 .ini 檔案…"
    INFO_OVER_DOWN = "所有操作皆已完成。"
    INFO_ENTER_ANY_KEY_CONTINUE = "請按任意鍵結束本腳本。"

    WARN_REMERGE_CHECK = "\x1b[33m如果是重新合併已合併的 Mod，請輸入 '-e'，否則請回車空行繼續。\x1b[0m\n"

    ERROR_INI_NOT_FOUND_1 = "\x1b[31m\n找不到 .ini 文件 - 請確保 mod 文件夾與此腳本在同一個文件夾中。\x1b[0m"
    ERROR_INI_NOT_FOUND_2 = "\x1b[31m如果在已經屬於切換 mod 的一組文件上使用此腳本，請使用 -e 選項啟用 .ini 文件並重新生成合併的 ini\x1b[0m\n"
    ERROR_TOGGLE_KEY = "\n\x1b[31m按鍵無法識別，必須是一個單獨的字母\x1b[0m\n"
    ERROR_TO_MORE_ENTER_ORDER = "\n\x1b[31m錯誤：只能輸入欲合併的模組的數量\x1b[0m\n"
    ERROR_DUPLIVATE_ORDER = "\n\x1b[31m錯誤：每個模組的編號最多只能輸入一次\x1b[0m\n"
    ERROR_INDEX_OVER_RANGE = "\n\x1b[31m錯誤：所選縮引值大於可用的最大索引值\x1b[0m\n"
    ERROR_INDEX_LESS_ZERO = "\n\x1b[31m錯誤：所選縮引值小於 0\x1b[0m\n"
    ERROR_ENTER = "\n\x1b[31m錯誤：只能輸入您要合併的模組的索引，並請用空格分隔（例如：3 0 1 2）\x1b[0m\n"


def main():
    parser = argparse.ArgumentParser(description=Message.ARG_DISCRIPTION.value)
    parser.add_argument("-r", "--root", type=str, default=".", help=Message.ARG_HELP_ROOT)
    parser.add_argument("-s", "--store", action="store_true", help="在完成後保留原始的 .ini 文件啟用狀態")
    parser.add_argument("-e", "--enable", action="store_true", help="重新啟用已禁用的 .ini 文件")
    parser.add_argument("-n", "--name", type=str, default="merged.ini", help="最終 .ini 文件的名稱")
    parser.add_argument("-k", "--key", type=str, default="", help="切換mod所需的按鍵")
    parser.add_argument("-c", "--compress", action="store_true", help="使輸出的mod盡可能小（警告：難以還原，建議備份）")
    parser.add_argument("-a", "--active", action="store_true", default=True, help="僅在切換時更換活動角色")
    parser.add_argument("-ref", "--reflection", action="store_true", help="為3.0+角色應用反射修復")

    args = parser.parse_args()

    print(Message.INFO_TITLE.value)

    enable = input(Message.WARN_REMERGE_CHECK.value)
    if enable == "-e":
        args.enable = True

    if args.active:
        print(Message.INFO_ACTIVE.value)

    if args.enable:
        print(Message.INFO_ENABLE.value)
        enable_ini(args.root)
        print()

    if not args.store:
        print(Message.INFO_STORE_1.value)
        print(Message.INFO_STORE_2.value)
        print(Message.INFO_STORE_3.value)

    if args.compress:
        print(Message.INFO_COMPRESS.value)

    print(Message.INFO_INI_SEARCH.value)
    ini_files = collect_ini(args.root, args.name)

    if not ini_files:
        print(Message.ERROR_INI_NOT_FOUND_1.value)
        print(Message.ERROR_INI_NOT_FOUND_2.value)
        input(Message.INFO_ENTER_ANY_KEY_CONTINUE.value)
        return

    print(Message.INFO_INI_FOUND.value)
    for i, ini_file in enumerate(ini_files):
        print(f"\t{i}:  {ini_file}")

    print(Message.INFO_HOW_THIS_WORK_1.value)
    print(Message.INFO_HOW_THIS_WORK_2.value)
    print(Message.INFO_HOW_THIS_WORK_3.value)
    ini_files = get_user_order(ini_files)

    if args.key:
        key = args.key
    else:
        print()
        key = input(Message.INFO_TOGGLE_KEY.value)
        while not key or len(key) != 1:
            print(Message.ERROR_TOGGLE_KEY.value)
            key = input()
        key = key.lower()

    constants =    "; Constants ---------------------------\n\n"
    overrides =    "; Overrides ---------------------------\n\n"
    shader    =    "; Shader ------------------------------\n\n"
    commands  =    "; CommandList -------------------------\n\n"
    resources =    "; Resources ---------------------------\n\n"

    swapvar = "swapvar"
    constants += f"[Constants]\nglobal persist ${swapvar} = 0\n"
    if args.active:
        constants += f"global $active\n"
    if args.reflection:
        constants += f"global $reflection\n"
    constants += "global $creditinfo = 0\n"
    constants += f"\n[KeySwap]\n"
    if args.active:
        constants += f"condition = $active == 1\n"
    constants += f"key = {key}\ntype = cycle\n${swapvar} = {','.join([str(x) for x in range(len(ini_files))])}\n$creditinfo = 0\n\n"
    if args.active or args.reflection:
        constants += f"[Present]\n"
    if args.active:
        constants += f"post $active = 0\n"
    if args.reflection:
        constants += f"post $reflection = 0\n"



    print(Message.INFO_INI_PARSING.value)
    all_mod_data = []
    ini_group = 0
    for ini_file in ini_files:
        with open(ini_file, "r", encoding="utf-8") as f:
            ini_text = ["["+x.strip() for x in f.read().split("[")]
            for section in ini_text[1:]:
                mod_data = parse_section(section)
                mod_data["location"] = os.path.dirname(ini_file)
                mod_data["ini_group"] = ini_group
                all_mod_data.append(mod_data)
        ini_group += 1

    if [x for x in all_mod_data if "name" in x and x["name"].lower() == "creditinfo"]:
        constants += "run = CommandListCreditInfo\n\n"
    else:
        constants += "\n"

    if [x for x in all_mod_data if "name" in x and x["name"].lower() == "transparency"]:
        shader += """[CustomShaderTransparency]
blend = ADD BLEND_FACTOR INV_BLEND_FACTOR
blend_factor[0] = 0.5
blend_factor[1] = 0.5
blend_factor[2] = 0.5
blend_factor[3] = 1
handling = skip
drawindexed = auto

"""

    print(Message.INFO_CALUCUATING_OVR_RES_SECTION.value)
    command_data = {}
    seen_hashes = {}
    reflection = {}
    n = 1
    for i in range(len(all_mod_data)):
        # Overrides. Since we need these to generate the command lists later, need to store the data
        if "hash" in all_mod_data[i]:
            index = -1
            if "match_first_index" in all_mod_data[i]:
                index = all_mod_data[i]["match_first_index"]
            # First time we have seen this hash, need to add it to overrides
            if (all_mod_data[i]["hash"], index) not in command_data:
                command_data[(all_mod_data[i]["hash"], index)] = [all_mod_data[i]]
                overrides += f"[{all_mod_data[i]['header']}{all_mod_data[i]['name']}]\nhash = {all_mod_data[i]['hash']}\n"
                if index != -1:
                    overrides += f"match_first_index = {index}\n"
                # These are custom commands GIMI implements, they do not need a corresponding command list
                if "VertexLimitRaise" not in all_mod_data[i]["name"]:
                    overrides += f"run = CommandList{all_mod_data[i]['name']}\n"
                if index != -1 and args.reflection:
                    overrides += f"ResourceRef{all_mod_data[i]['name']}Diffuse = reference ps-t1\nResourceRef{all_mod_data[i]['name']}LightMap = reference ps-t2\n$reflection = {n}\n"
                    reflection[all_mod_data[i]['name']] = f"ResourceRef{all_mod_data[i]['name']}Diffuse,ResourceRef{all_mod_data[i]['name']}LightMap,{n}"
                    n+=1
                if args.active:
                    if "Position" in all_mod_data[i]["name"]:
                        overrides += f"$active = 1\n"

                overrides += "\n"
            # Otherwise, we have seen the hash before and we just need to append it to the commandlist
            else:
                command_data[(all_mod_data[i]["hash"], index)].append(all_mod_data[i])
        elif "header" in all_mod_data[i] and "CommandList" in all_mod_data[i]["header"]:
            command_data.setdefault((all_mod_data[i]["name"],0),[]).append(all_mod_data[i])
        # Resources
        elif "filename" in all_mod_data[i] or "type" in all_mod_data[i]:

            resources += f"[{all_mod_data[i]['header']}{all_mod_data[i]['name']}.{all_mod_data[i]['ini_group']}]\n"
            for command in all_mod_data[i]:
                if command in ["header", "name", "location", "ini_group"]:
                    continue
                if command == "filename":
                    with open(f"{all_mod_data[i]['location']}\\{all_mod_data[i][command]}", "rb") as f:
                        sha1 = hashlib.sha1(f.read()).hexdigest()
                    if sha1 in seen_hashes and args.compress:
                        resources += f"{command} = {seen_hashes[sha1]}\n"
                        os.remove(f"{all_mod_data[i]['location']}\\{all_mod_data[i][command]}")
                    else:
                        seen_hashes[sha1] = f"{all_mod_data[i]['location']}\\{all_mod_data[i][command]}"
                        resources += f"{command} = {all_mod_data[i]['location']}\\{all_mod_data[i][command]}\n"
                else:
                    resources += f"{command} = {all_mod_data[i][command]}\n"
            resources += "\n"

    if args.reflection:
        print(Message.INFO_FIXXING_CHARACTER_SHADER.value)
        refresources = ''
        CommandPart = ['ReflectionTexture', 'Outline']
        shadercode = """
[ShaderRegexCharReflection]
shader_model = ps_5_0
run = CommandListReflectionTexture
[ShaderRegexCharReflection.pattern]
discard_n\w+ r\d\.\w+\\n
lt r\d\.\w+, l\(0\.010000\), r\d\.\w+\\n
and r\d\.\w+, r\d\.\w+, r\d\.\w+\\n

[ShaderRegexCharOutline]
shader_model = ps_5_0
run = CommandListOutline
[ShaderRegexCharOutline.pattern]
mov o0\.w, l\(0\)\\n
mov o1\.xyz, r0\.xyzx\\n
        """
        shader += f"{shadercode}\n"
        for i in range(len(CommandPart)):
            ref  = f"[CommandList{CommandPart[i]}]\n"
            ref += f"if $reflection != 0\n\tif "
            for x in reflection:
                r = reflection[x].split(",")
                ref += f"$reflection == {r[2]}\n"
                ps = [['ps-t0','ps-t1'],['ps-t1','ps-t2']]
                ref += f"\t\t{ps[i][0]} = copy {r[0]}\n\t\t{ps[i][1]} = copy {r[1]}\n"
                ref += f"\telse if "
                if i == 0:
                    refresources += f"[{r[0]}]\n[{r[1]}]\n"
            ref = ref.rsplit("else if",1)[0] + "endif\n"
            ref += f"drawindexed=auto\n"
            ref += f"$reflection = 0\n"
            ref += f"endif\n\n"
            commands += ref

    print(Message.INFO_CREATING_CMD_SECTION.value)
    tabs = 1

    for hash, index in command_data:
        if "VertexLimitRaise" in command_data[(hash, index)][0]["name"]:
            continue
        commands += f"[CommandList{command_data[(hash, index)][0]['name']}]\nif "
        for model in command_data[(hash, index)]:
            commands += f"${swapvar} == {model['ini_group']}\n"
            for command in model:
                if command in ["header", "name", "hash", "match_first_index", "location", "ini_group"]:
                    continue

                if command == "endif":
                    tabs -= 1
                    for i in range(tabs):
                        commands += "\t"
                    commands += f"{command}"
                elif "else if" in command:
                    tabs -= 1
                    for i in range(tabs):
                        commands += "\t"
                    commands += f"{command} = {model[command]}"
                    tabs += 1
                else:
                    for i in range(tabs):
                        commands += "\t"
                    if command[:2] == "if" or command[:7] == "else if":
                        commands += f"{command} == {model[command]}"
                    else:
                        commands += f"{command} = {model[command]}"
                    if command[:2] == "if":
                        tabs += 1
                    elif (command[:2] in ["vb", "ib", "ps", "vs", "th"] or "Resource" in model[command]) and model[command].lower() != "null":
                        commands += f".{model['ini_group']}"
                commands += "\n"
            commands += "else if "
        commands = commands.rsplit("else if",1)[0] + "endif\n\n"

    print(Message.INFO_OUTPUT_RUNNING_RESULTS.value)
    result = f"; 合併的 Mod: {', '.join([x for x in ini_files])}\n\n"
    if args.reflection:
        result += f"{refresources}\n"
    result += constants
    result += shader
    result += overrides
    result += commands
    result += resources
    if args.reflection:
        result += "\n\n; For fixing green reflections and broken outlines colors on 3.0+ characters\n"
    else:
        result += "\n\n"
    result += "; .ini generated by GIMI (Genshin-Impact-Model-Importer) mod merger script\n"

    result += "; If you have any issues or find any bugs, please open a ticket at https://github.com/SilentNightSound/GI-Model-Importer/issues or contact SilentNightSound#7430 on discord"

    with open(args.name, "w", encoding="utf-8") as f:
        f.write(result)

    if not args.store:
        print(Message.INFO_CALER_DISABLE_EACH_INI.value)
        for file in ini_files:
            os.rename(file, os.path.join(os.path.dirname(file), "DISABLED") + os.path.basename(file))


    print(Message.INFO_OVER_DOWN.value)
    input(Message.INFO_ENTER_ANY_KEY_CONTINUE.value)


# Collects all .ini files from current folder and subfolders
def collect_ini(path, ignore):
    ini_files = []
    for root, dir, files in os.walk(path):
        if "disabled" in root.lower():
            continue
        for file in files:
            if "disabled" in file.lower() or ignore.lower() in file.lower():
                continue
            if os.path.splitext(file)[1] == ".ini":
                ini_files.append(os.path.join(root, file))
    return ini_files

# Re-enables disabled ini files
def enable_ini(path):
    for root, dir, files in os.walk(path):
        for file in files:
            if os.path.splitext(file)[1] == ".ini" and ("disabled" in root.lower() or "disabled" in file.lower()):
                print(f"\tRe-enabling {os.path.join(root, file)}")
                new_path = re.compile("disabled", re.IGNORECASE).sub("", os.path.join(root, file))
                os.rename(os.path.join(root, file), new_path)


# Gets the user's preferred order to merge mod files
def get_user_order(ini_files):

    choice = input()

    # User entered data before pressing enter
    while choice:
        choice = choice.strip().split(" ")

        if len(choice) > len(ini_files):
            print(Message.ERROR_TO_MORE_ENTER_ORDER.value)
            choice = input()
        else:
            try:
                result = []
                choice = [int(x) for x in choice]
                if len(set(choice)) != len(choice):
                    print(Message.ERROR_DUPLIVATE_ORDER.value)
                    choice = input()
                elif max(choice) >= len(ini_files):
                    print(Message.ERROR_INDEX_OVER_RANGE.value)
                    choice = input()
                elif min(choice) < 0:
                    print(Message.ERROR_INDEX_LESS_ZERO.value)
                    choice = input()
                    print()
                else:
                    for x in choice:
                        result.append(ini_files[x])
                    return result
            except ValueError:
                print(Message.ERROR_ENTER.value)
                choice = input()

    # User didn't enter anything and just pressed enter
    return ini_files


# Parses a section from the .ini file
def parse_section(section):
    mod_data = {}
    recognized_header = ("[TextureOverride", "[ShaderOverride", "[Resource", "[Constants", "[Present", "[CommandList", "[CustomShader")
    for line in section.splitlines():
        if not line.strip() or line[0] == ";":  # comments and empty lines
            continue

        # Headers
        for header in recognized_header:
            if header in line:
                # I give up on trying to merge the reflection fix, it's way too much work. Just re-apply after merging
                if "CommandListReflectionTexture" in line or "CommandListOutline" in line:
                    return {}
                mod_data["header"] = header[1:]
                mod_data["name"] = line.split(header)[1][:-1]
                break
        # Conditionals
        if "==" in line:
            key, data = line.split("==",1)
            mod_data[key.strip()] = data.strip()
        elif "endif" in line:
            key, data = "endif", ""
            mod_data[key.strip()] = data.strip()
        # Properties
        elif "=" in line:
            key, data = line.split("=")
            # See note on reflection fix above
            if "CharacterIB" in key or "ResourceRef" in key:
                continue

            mod_data[key.strip()] = data.strip()

    return mod_data


def config_state_colored_text(v: bool):
    if v == True:
        return "\x1b[32mTrue\x1b[0m"
    else:
        return "\x1b[31mFalse\x1b[0m"


if __name__ == "__main__":
    # print("\x1b[31mTExt\x1b[0m")
    main()
