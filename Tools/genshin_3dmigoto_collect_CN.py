# Author: SilentNightSound#7430
# Collects and organizes the relevant object model data from a frame dump, outputting it in a format
# that the Blender 3Dmigoto plugin recognizes

# Currently only tested for genshin, but may work for other mihoyo games if they are similar enough

import os
import sys
import argparse
import shutil
import json
import re

def main():
    parser = argparse.ArgumentParser(description="從 3dmigoto 幀轉儲收集並編譯模型數據")
    parser.add_argument("-vb", nargs="+", type=str, help="角色繪製使用的主要 VBs。將 X 作為前綴添加到 hash 僅轉儲紋理而不轉儲模型數據（e.g. 對於面部）")
    parser.add_argument("-n", "--name", type=str, help="在資料夾與輸出文件上使用的角色名稱。")
    parser.add_argument("-c", "--component_names", nargs="*", type=stripped_string, help="組件的自定義名稱。如沒有指定，默認為數字。")
    parser.add_argument("-f", "--framedump", type=str, help="幀轉儲資料夾的名稱。如沒有指定，則使用最新的一個。")
    parser.add_argument("-vs", type=str, default="653c63ba4a73ca8b", help="角色模型的 Root VS")
    parser.add_argument("--force", "--force_draw", nargs="+", help="強制解析器從指定 draw ids 收集數據。")
    parser.add_argument("--force_object", help="強制解析器從指定 root 對象收集數據。")
    parser.add_argument("--remove_sanity", action='store_true', help="關閉健全性檢查，這對於故障排除很有用。Also how I'm feeling after debugging this all day.")
    parser.add_argument("--has_blend", action='store_true', help="強制解析器嘗試收集 blend data")
    parser.add_argument("--no_blend", action='store_true', help="強制解析器跳過收集 blend data")
    parser.add_argument("--has_normalmap", action='store_true', help="除其他紋理貼圖，模型還有法線貼圖。")
    args = parser.parse_args()

    if True:
        #必要參數檢查
        if not args.name:
            print("沒有輸入資料夾名稱，正在退出...")
            print("請使用 -n 來建立輸出資料夾的名稱，通常是角色名稱，不建議使用中文。")
            return
        if not args.vb:
            print("沒有輸入 VB hash，正在退出...")
            print("請使用 -vb 來指定需要收集的對象的 hash，允許複數。")
            return

    character = args.name.replace(" ", "")
    base_classification = ["Head", "Body", "Dress", "Extra"]

    # Even if user doesn't specify specific framedump, code will now default to the most recent one
    # Frame analysis folders have leading 0s for the date, so default order will be sorted correctly
    if args.framedump:
        frame_dump_folder = args.framedump
    else:
        print("尋找最新的轉儲資料夾...")
        frame_dump_folder = [x for x in os.listdir(".") if "FrameAnalysis" in x][-1]
        print(f"發現資料夾：{frame_dump_folder}")

    # Was getting tired of accidentally deleting folder contents when making typos
    print("建立輸出資料夾...")
    if not os.path.isdir(character):
        os.mkdir(character)
    else:
        # print(f"警告：Everything currently in the {character} folder will be overwritten - make sure any important files are backed up. Press any button to continue")
        print(f"警告：'{character}' 文件夾中的所有資料都將被覆蓋 - 確保備份所有的重要文件。按任意按鈕繼續。")
        input()

    # First pass to give us the VB for the position and blend data
    # Now, instead of just collecting one object corresponding to the root vs we collect all of them and double check
    #   later that the one we collected matches the vertex size of the texcoord
    point_vbs = collect_pointlist_candidates(frame_dump_folder, args.vs)

    # Second pass gives us all the relevant IDs that correspond to the vbs we are searching for
    # Have extended this to now collect data for multiple vbs at once for characters drawn across buffers
    # It would be more efficient to collect this and pointlist in one pass, but framedumps are usually fairly small
    #   and there are some cases where we want to keep these logically separated
    relevant_ids, first_vss = collect_relevant_ids(frame_dump_folder, args.vb)

    # Third pass to collect IBs, texcoord VB, and diffuse/light maps
    # At this point, we are assuming that the positional data is going to come from the pointlists - if that assumption
    #   is proven wrong later on in the script, we will use the position vbs collected here instead
    model_data, position_vbs, texcoord_vbs = collect_model_data(frame_dump_folder, relevant_ids, args.force)

    # For constructing the .ini file
    # New file structure allows for multiple vbs to be contained in a single file
    hash_data = []

    # We are now potentially constructing multiple objects - in the case where length=1, behaviour is the same as before
    for i in range(len(model_data)):

        hash_data.append({})
        if args.component_names:
            hash_data[i]["component_name"] = args.component_names[i].replace(" ", "")
        elif i>0:
            hash_data[i]["component_name"] = f"{i+1}"
        else:
            hash_data[i]["component_name"] = ""

        texture_only = False
        if args.vb[i][0].lower() == "x":
            print("跳過緩衝區數據，僅收集紋理資源。")
            vb_merged = ""
            position_vb = ""
            texture_only = True

        # Some objects do not have a separate vb1, and all the data is contained in vb0
        elif not texcoord_vbs[i]:
            position_vb = position_vbs[i]
            buffer_data, element_format = collect_buffer_data(frame_dump_folder, position_vb, ["POSITION:", "NORMAL:", "COLOR:", "TEXCOORD:", "TEXCOORD1:", "TANGENT:"])
            vb_merged = construct_combined_buffer(buffer_data, element_format)
        else:
            # Re-arranging collection order. By collecting texcoord first, we can use its length to figure out which of the
            #   position/blend vbs are correct (or if there even is a corresponding pointlist)
            # Some characters have one texcoord, others have two, varies from character to character
            # Order is COLOR (R8G8B8A8_UNORM), TEXCOORD (R32G32_FLOAT), *TEXCOORD1 (R32G32_FLOAT) if it exists
            # Sizes are 4, 8, *8 for a total of either 12 or 20
            print(f"\n從 {texcoord_vbs[i]} 收集 texcoord 數據")
            texcoord_stride = get_stride(os.path.join(frame_dump_folder, texcoord_vbs[i]))

            texcoord_filter = ["COLOR:", "TEXCOORD:"]
            if texcoord_stride == "20":
                texcoord_filter.append("TEXCOORD1:")
            texcoord_filter = tuple(texcoord_filter)

            texcoord, texcoord_format = collect_buffer_data(frame_dump_folder, texcoord_vbs[i], texcoord_filter)

            # Attempt to find the pointlist corresponding to the texture coordinate by comparing sizes
            print("嘗試尋找對應的場景對象...")
            point_vb_candidates = [x for x in point_vbs if point_vbs[x]["vertex_count"] == len(texcoord)]

            if args.has_blend and not point_vb_candidates:
                print("錯誤：無法找到匹配的 blend 坐標。請指定要與 --force 一起使用的 draw IDs")
                return

            if not args.no_blend and not point_vb_candidates:
                print("警告：無法找到用於位置信息的 vbs")
                return

            if args.no_blend or (not args.force_object and not point_vb_candidates):
                # If we can't find a correct pointlist, fall back to using the positional data from collect_model_data
                print(f"警告：無法找到任何長度與 texcoord ({len(texcoord)}) 匹配的 vbs 點。默認使用來自更高層的 draw IDs 的位置數據。")
                print("跳過混合數據收集。")
                position_vb = position_vbs[i]
                blend = []
                blend_vb = "="
                hash_data[i]["root_vs"] = ""
            else:
                # Otherwise, we have found at least one corresponding pointlist which we can use to collect the position data
                # If more than one, we have no way of distinguishing so we have to ask the user
                if len(point_vb_candidates) > 1:
                    selection = input(f"錯誤：發現太多具有 vertex count {len(texcoord)} 的候選對象。請從以下列表輸入正確對象的 ID：{point_vb_candidates}\n>> ")
                    point_vb_candidates =  [selection]

                # Forces a specific object, sometimes there is a mismatch so this can be used for troubleshooting
                if args.force_object:
                    correct_vb_id = args.force_object
                else:
                    correct_vb_id = point_vb_candidates[0]
                print(f"使用 ID 為 {correct_vb_id} 的對象。")
                position_vb = point_vbs[correct_vb_id]["position_vb"]
                blend_vb = point_vbs[correct_vb_id]["blend_vb"]

                # Order is BLENDWEIGHT (R32G32B32A32_FLOAT), BLENDINDICES (R32G32B32A32_SINT)
                # Sizes are 16,16 for a total stride of 32
                # Only exists if we found a pointlist
                print(f"從 {blend_vb} 收集 blend 數據")
                blend, blend_format = collect_buffer_data(frame_dump_folder, blend_vb, ("BLENDWEIGHT:", "BLENDINDICES:"))

                hash_data[i]["root_vs"] = args.vs


            # Positional data exists for both of the above cases, though the file we get the info from differs
            # Order is POSITION (R32G32B32_FLOAT), NORMAL (R32G32B32_FLOAT), TANGENT (R32G32B32A32_FLOAT)
            # Sizes are 12, 12, 16 for a total stride of 40
            # All other values ignored
            print(f"從 {position_vb} 收集 Position 數據")
            position, position_format = collect_buffer_data(frame_dump_folder, position_vb, ("POSITION:", "NORMAL:", "TANGENT:"))


            # If we have to continue because of super force, need to equalize the files
            if args.remove_sanity:
                max_vertices = min(len(position), len(blend), len(texcoord))
                position = position[:max_vertices]
                blend = blend[:max_vertices]
                texcoord = texcoord[:max_vertices]

            # Sanity check
            # If position, blend and texcoord are not the same length we cannot construct an output file
            if blend and (len(position) != len(blend) or len(blend) != len(texcoord)):
                print(f"\n錯誤：緩衝區之間的大小不匹配。Position: {len(position)}, Blend: {len(blend)}, Texcoord: {len(texcoord)}.")
                print("這個問題通常是因為程式無法識別正確的對象而嘗試合併不兼容的對象")
                print("嘗試檢查幀轉儲，並使用 --force 告訴程式要使用什麼 draw ID")

                print("如果你想繼續轉儲該對象，請輸入 y（請注意，它將出現有問題的導出並且無法正確重新導入到遊戲中）")
                user_input = input()
                if user_input == "y":
                    max_vertices = min(len(position), len(blend), len(texcoord))
                    position = position[:max_vertices]
                    blend = blend[:max_vertices]
                    texcoord = texcoord[:max_vertices]
                else:
                    print("退出程式。")
                    return

            buffer_data = []
            for j in range(len(position)):
                temp = []
                temp.extend(position[j])
                if blend:
                    temp.extend(blend[j])
                temp.extend(texcoord[j])
                buffer_data.append(temp)
            element_format = position_format
            if blend:
                element_format.extend(blend_format)
            element_format.extend(texcoord_format)

            vb_merged = construct_combined_buffer(buffer_data, element_format)

        # Now that we have all the buffer data, assemble and output the final results to the folder
        output_results(frame_dump_folder, character, args.component_names, model_data, vb_merged, position_vb, i, texture_only, base_classification, args.has_normalmap)

        # And save the hash data to the dictionary
        print("\n將角色 hash 信息添加到 hash 文件(hash.json)中")
        if texture_only:
            position_vb_hash = ""
            blend_vb_hash = ""
            texcoord_vb_hash = ""
            ib_hash = ""
            draw_vb = ""
        elif not texcoord_vbs[i]:
            position_vb_hash = position_vb.split("=")[1].split("-")[0]
            blend_vb_hash = ""
            texcoord_vb_hash = ""
            ib_hash = model_data[i][0][0].split("=")[1].split("-")[0]
            draw_vb = args.vb[i]
        else:
            print(model_data)
            position_vb_hash = position_vb.split("=")[1].split("-")[0]
            blend_vb_hash = blend_vb.split("=")[1].split("-")[0]
            texcoord_vb_hash = texcoord_vbs[i].split("=")[1].split("-")[0]
            ib_hash = model_data[i][0][0].split("=")[1].split("-")[0]
            draw_vb = args.vb[i]
        object_indexes = sorted(model_data[i].keys())
        texture_hashes = []
        for index in object_indexes:
            texture_group = []
            seen_hashes = set()
            for j, texture in enumerate(model_data[i][index][1:]):
                texture_hash = texture.split("-vs=")[0].split("=")[-1]
                if texture_hash not in seen_hashes:
                    seen_hashes.add(texture_hash)
                    extension = ".dds"
                    if j==0:
                        if args.has_normalmap:
                            texture_type = "NormalMap"
                        else:
                            texture_type = "Diffuse"
                    elif j==1:
                        if args.has_normalmap:
                            texture_type = "Diffuse"
                        else:
                            texture_type = "LightMap"
                    elif j==2 and args.has_normalmap:
                        texture_type = "LightMap"
                    else:
                        extension, texture_type = identify_texture(frame_dump_folder, texture)
                        if [x for x in texture_group if texture_type == x[0]]:
                            texture_type = f"t{j}"
                    texture_group.append([texture_type, extension, texture_hash])
            texture_hashes.append(texture_group)

        if len(object_indexes) <= len(base_classification):
            object_classifications = base_classification[:len(object_indexes)]
        else:
            object_classifications = base_classification
            count = 2
            while len(object_classifications) < len(object_indexes):
                object_classifications.append(f"{base_classification[-1]}{count}")
                count += 1

        hash_data[i]["draw_vb"] = draw_vb
        hash_data[i]["position_vb"] = position_vb_hash
        hash_data[i]["blend_vb"] = blend_vb_hash
        hash_data[i]["texcoord_vb"] = texcoord_vb_hash
        hash_data[i]["ib"] = ib_hash
        hash_data[i]["object_indexes"] = object_indexes
        hash_data[i]["object_classifications"] = object_classifications
        hash_data[i]["texture_hashes"] = texture_hashes
        hash_data[i]["first_vs"] = first_vss[i]

    # Finally, we save the hash data in the output folder
    # I'm choosing a different name from hash_info.json on purpose to prevent confusion
    with open(os.path.join(character, "hash.json"), "w") as f:
        json.dump(hash_data, f, indent=4)

    print("所有操作皆完成，退出程式。")


# Collect potential candidates for the pointlist buffers
# These contain information about the model before it is posed, along with blend-related data
# May not exist for certain objects, depending how they are bound to bones, and have seen cases where there is a
#   size mismatch between these buffers and the later ones that are drawn to the screen
# Every example I have seen so far uses VS hash 653c63ba4a73ca8b (even between games), but not sure if that is unique or not
def collect_pointlist_candidates(frame_dump_folder, root_vs_hash="653c63ba4a73ca8b"):
    print("搜索 root VS 對應的 VB")
    point_vbs = {}
    frame_dump_files = os.listdir(frame_dump_folder)
    for filename in frame_dump_files:
        draw_id = filename.split("-")[0]
        if root_vs_hash in filename and "-vb0=" in filename and os.path.splitext(filename)[1] == ".txt":
            with open(os.path.join(frame_dump_folder, filename), "r") as f:
                vertex_count = int([x for x in f.readlines() if "vertex count:" in x][0].split(": ")[1])
            print(f"找到 position VB: {filename}, vertex count: {vertex_count}")
            point_vbs[draw_id] = {"vertex_count": vertex_count, "position_vb": filename}
        if root_vs_hash in filename and "-vb1=" in filename and os.path.splitext(filename)[1] == ".txt":
            print(f"找到 blend VB: {filename},  vertex count: {vertex_count}")
            point_vbs[draw_id]["blend_vb"] = filename

    # Previous version would return a failure here, but there are objects without corresponding pointlist buffers
    if not point_vbs:
        print("警告：無法找到root position 與 blend VB。假設不存在並繼續後續動作。")

    return point_vbs


# Collects all draw ids that correspond to the vb hashes the user entered
# These usually contain things like the textures, ibs and color/texcoord
# They also contain position data, but these buffers are after the character have been posed so they are less useful
def collect_relevant_ids(frame_dump_folder, draw_vb_hashes, use_lower=False):
    relevant_ids = []
    relevant_ids_size = []
    relevant_ids_first_index = []
    first_vss = []
    frame_dump_files = os.listdir(frame_dump_folder)
    for draw_vb_hash in draw_vb_hashes:
        texture_only_flag = False
        # X is being used to control what draw ids have textures only dumped, and is propagated through the variables
        if draw_vb_hash[0].lower() == "x":
            draw_vb_hash = draw_vb_hash[1:]
            texture_only_flag = True
        relevant_id_group = []
        relevant_id_size_group = []
        relevant_ids_first_index_group = []
        first_vs = ""
        for filename in frame_dump_files:
            if draw_vb_hash in filename:
                draw_id = filename.split("-")[0]
                # The first vs used to draw the character isn't currently used, but there is some potential future use
                if not first_vs and int(draw_id) > 10:
                    first_vs = filename.split("vs=")[1].split("-")[0]
                    print(f"\n找到 first VS: {first_vs}")
                # I still don't really understand what the lower ids that show up sometimes are for, but there needs
                #   to be some method of allowing them to be used in case the object we are scraping is one of the few in the scene
                if draw_id not in relevant_id_group and (use_lower or int(draw_id)>10):
                    if texture_only_flag:
                        draw_id = "x" + draw_id
                    relevant_id_group.append(draw_id)
                    if os.path.splitext(filename)[1] == ".buf":
                        filename = filename.replace(".buf", ".txt")
                    with open(os.path.join(frame_dump_folder, filename), "r") as f:
                        vertex_count = int([x for x in f.readlines() if "vertex count:" in x][0].split(": ")[1])

                    ib_filename = [x for x in frame_dump_files if draw_id in x and "-ib=" in x and ".txt" in x]
                    if ib_filename:
                        with open(os.path.join(frame_dump_folder, ib_filename[0]), "r") as f:
                            first_index = int([x for x in f.readlines() if "first index:" in x][0].split(": ")[1])

                    relevant_ids_first_index_group.append(str(first_index).rjust(6))
                    relevant_id_size_group.append(str(vertex_count).rjust(6))


        relevant_ids.append(relevant_id_group)
        relevant_ids_size.append(relevant_id_size_group)
        relevant_ids_first_index.append(relevant_ids_first_index_group)
        first_vss.append(first_vs)

    if not use_lower and not any(relevant_ids):
        print("警告：無法找到任何相關的 IDs。請檢查確認 IDs < 10 的可能性")
        relevant_ids, first_vss = collect_relevant_ids(frame_dump_folder, draw_vb_hashes, use_lower=True)
    else:
        print("相關的 IDs:")
        for i in range(len(relevant_ids)):
            print(f"\t組件 {i+1} IDs         : {relevant_ids[i]}")
            print(f"\t組件 {i+1} Vertex Count: {relevant_ids_size[i]}")
            print(f"\t組件 {i+1} First Index : {relevant_ids_first_index[i]}")

    return relevant_ids, first_vss


# Collects model data (ib, color, texcoord(s), textures)
# Positional data comes from the pointlists, but can force it to be collected from these buffers by using the flag
def collect_model_data(frame_dump_folder, relevant_ids, force_ids):
    model_data = []
    position_vbs = []
    texcoord_vbs = []

    # A couple of characters have unique draw call formats, this forces a specific list of ids to be parsed
    # Also good for troubleshooting
    if force_ids:
        print(f"忽略找到的 ID 並強制分析 ID {force_ids}")
        relevant_ids = [force_ids]

    for id_group in relevant_ids:

        model_group = {}
        texcoord_vb = ""
        position_vb = ""
        texcoord_largest_count = -1
        position_largest_count = -1

        # Updating this. The previous method used calls that came in pair/triples to find the objects from the scene,
        #   but there are several characters that have their object draw calls split up and which fail as a result
        # Now, we continue to collect until we find a duplicate object (I'm pretty sure there are no characters which
        #   draw one of their components twice before drawing all of their components at least once)
        frame_dump_files = os.listdir(frame_dump_folder)
        for current_id in id_group:

            texture_only = False
            if current_id[0].lower() == "x":
                current_id = current_id[1:]
                texture_only = True

            current_id_files = [name for name in frame_dump_files if f"{current_id}-" in name]

            # Collecting IB file for portion of model being drawn on the current id
            # This should always exist, and the format should be standard across all games
            draw_ib = [name for name in current_id_files if "-ib=" in name and os.path.splitext(name)[1] == ".txt"]
            if len(draw_ib) != 1:
                print(f"錯誤：無法找到 draw ID {current_id} 對應的 IB。正在退出...")
                sys.exit()
            draw_ib = draw_ib[0]

            with open(os.path.join(frame_dump_folder, draw_ib), "r") as f:
                first_index = -1
                for line in f.readlines():
                    if "first index:" in line:
                        first_index = int(line.split(":")[1].strip())
                        break
                if first_index < 0:
                    print("錯誤：無法識別的 IB 格式。正在退出...")
                    sys.exit()
            print(f"\nID: {current_id}，在索引 {first_index} 處找到對象。")

            # It turns out that not all objects have adjacent draw calls
            if first_index in model_group and not force_ids:
                print("到達重複對象。跳過並繼續。")
                continue

            # Re-arranging texture collection to be earlier
            # I had previously assumed that all relevant ids would contain textures, but it turns out sometimes the
            #   lower id values do not for whatever reason
            # The original script only used the diffuse and lightmaps, but I have extended to now look for shadow
            #   ramps and metal maps as well
            texture_maps = [name for name in current_id_files if "-ps-t" in name and (
                        os.path.splitext(name)[1] == ".dds" or os.path.splitext(name)[1] == ".jpg")]
            print(f"找到 texture maps: {texture_maps}")
            if len(texture_maps) < 2:
                print(f"警告：無法找到 {current_id} 的 diffuse 和 lightmaps")

            model_group[first_index] = []
            model_group[first_index].append(texture_maps[0])
            if len(texture_maps) > 1 and "ps-t1" in texture_maps[1]:
                model_group[first_index].append(texture_maps[1])
            # Higher IDs are shadow ramps and metal maps for characters, and dissolve guides and noise patterns for weapons
            if len(texture_maps) > 2 and "ps-t2" in texture_maps[2]:
                model_group[first_index].append(texture_maps[2])
            if len(texture_maps) > 3 and "ps-t3" in texture_maps[3]:
                model_group[first_index].append(texture_maps[3])

            # Easier to add a blank value in place of the IB when dumping textures instead of rewriting everything to
            #   use variable lengths
            if texture_only:
                model_group[first_index].insert(0, "_")
            else:
                model_group[first_index].insert(0, draw_ib)

                # Even though each object technically has its own texcoord, they are all just portions of a single vb
                # The largest file will always contain the full texcoord for every point
                # I have yet to see a counter-example to this, but it is possible this will need to be done on a per-object
                #   basis and combined later if I ever find one
                texcoord_vb_candidate = [name for name in current_id_files if
                                         "-vb1=" in name and os.path.splitext(name)[1] == ".txt"]
                if len(texcoord_vb_candidate) == 1:
                    texcoord_vb_candidate = texcoord_vb_candidate[0]

                    # Previous version had an incorrect assumption that the largest file was also the one with the
                    #   highest vertex count, but it seems like the format can change even within a single object
                    #   leading to situations where a vb might have fewer vertices but a larger size
                    with open(os.path.join(frame_dump_folder, texcoord_vb_candidate), "r") as f:
                        texcoord_lines = f.readlines()
                        texcoord_count = int([x for x in texcoord_lines if "vertex count:" in x][0].split(": ")[1])
                        texcoord_exists = True
                        if not [x for x in texcoord_lines if "vertex-data:" in x]:
                            texcoord_exists = False
                    if texcoord_exists and texcoord_count > texcoord_largest_count:
                        print(f"新的最適配的 texcoord 候選：{current_id}")
                        texcoord_largest_count = texcoord_count
                        texcoord_vb = texcoord_vb_candidate

                # Same assumption needs to be changed for position too
                position_vb_candidate = [name for name in current_id_files if
                                         "-vb0=" in name and os.path.splitext(name)[1] == ".txt"][0]
                with open(os.path.join(frame_dump_folder, position_vb_candidate), "r") as f:
                    position_count = int([x for x in f.readlines() if "vertex count:" in x][0].split(": ")[1])
                if position_count > position_largest_count:
                    print(f"新的最適配的 position 候選：{current_id}")
                    position_largest_count = position_count
                    position_vb = position_vb_candidate

        if not model_group.keys():
            print(f"錯誤：無法找到任何模型組件。正在退出...")
            sys.exit()

        print(f"\n找到備份的 positional data: {position_vb}")
        print(f"找到 texcoord data: {texcoord_vb}")
        model_data.append(model_group)
        position_vbs.append(position_vb)
        texcoord_vbs.append(texcoord_vb)

    return model_data, position_vbs, texcoord_vbs


# Generalized function to collect data from buffer .txt
# This is more annoying to parse when compared to the raw .buf files, but the benefit is that each line already
#   has the corresponding name for the line as the prefix
def collect_buffer_data(frame_dump_folder, filename, filters):
    result = []
    ignore_normals = False
    with open(os.path.join(frame_dump_folder, filename), "r") as f:
        headers, data = f.read().split("vertex-data:\n")
        element_format = parse_buffer_headers(headers, data, filters)
        group_size = len(element_format)
        data = data.strip().split("\n")
        # The .txt files do not always accurately reflect what is in the raw data, can use this to filter
        temp = []
        for line in data:
            for filter in filters:
                if filter in line:
                    temp.append(line)
        data = temp
        vertex_group = []
        for i in range(len(data)):
            vertex = data[i].split(":")[1].strip().split(", ")
            if ignore_normals and element_format[i%len(element_format)]["semantic_name"] == "NORMAL":
                vertex[-1] = "0"
            elif element_format[i%len(element_format)]["semantic_name"] == "NORMAL" and len(vertex) == 4 and not vertex[-1] == '0':
                print(vertex)
                print("\n錯誤：識別出不正確的正常值。")
                print("程式將一些其他組件錯誤地識別為正常值")
                print("一般來說最好的解決方案是使用 --force 強製程式在不同的相關 ID 上運行")

                print("如果您想繼續像這樣轉儲對象，請輸入 y（必須在 Blender 中重新計算法線，並且可能會遇到重新導入的問題）")
                user_input = input()
                if user_input == "y":
                    ignore_normals = True
                    vertex[-1] = "0"
                else:
                    print("正在退出...")
                    sys.exit()

            vertex_group.append(vertex)

            if (i + 1) % group_size == 0:
                result.append(vertex_group)
                vertex_group = []

    return result, element_format


# Parsing the headers for vb0 txt files
# Note that the data in the headers is not super reliable - the byteoffset is almost always wrong, and the header
#   can contain more information than is actually in the file
def parse_buffer_headers(headers, data, filters):
    results = []
    # https://docs.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format
    for element in headers.split("]:")[1:]:
        lines = element.strip().splitlines()
        name = lines[0].split(": ")[1]
        if f"{name}:" not in data:
            continue
        index = lines[1].split(": ")[1]
        data_format = lines[2].split(": ")[1]
        # This value does not make any sense, so skip - it is not actually the normal but something else
        # if name == "NORMAL" and data_format == "R8G8B8A8_UNORM":
        #     print("WARNING: unrecognized normal format, skipping collection")
        #     continue
        bytewidth = sum([int(x) for x in re.findall("([0-9]*)[^0-9]", data_format.split("_")[0]+"_") if x])//8

        # A bit annoying, but names can be very similar so need to match filter format exactly
        element_name = name
        if index != "0":
            element_name += index
        if element_name+":" not in filters:
            continue

        results.append({"semantic_name": name, "element_name": element_name, "index": index, "format": data_format, "bytewidth": bytewidth})

    return results


# Constructs the output file that will be loaded into 3dmigoto
def construct_combined_buffer(buffer_data, element_format):
    print("\n構造 combined buffer")
    vb_merged = ""

    stride = 0
    for element in element_format:
        stride += element['bytewidth']
    vb_merged += f"stride: {stride}\n"
    vb_merged += f"first vertex: 0\nvertex count: {len(buffer_data)}\ntopology: trianglelist\n"

    element_offset = 0
    byte_offset = 0
    for element in element_format:
        vb_merged += f"element[{element_offset}]:\n  SemanticName: {element['semantic_name']}\n  SemanticIndex: {element['index']}\n  Format: {element['format']}\n  InputSlot: 0\n  AlignedByteOffset: {byte_offset}\n  InputSlotClass: per-vertex\n  InstanceDataStepRate: 0\n"
        element_offset += 1
        byte_offset += element['bytewidth']

    vb_merged += "\nvertex-data:\n\n"
    for i in range(len(buffer_data)):
        byte_offset = 0
        for j,element in enumerate(element_format):
            vb_merged += f"vb0[{i}]+{str(byte_offset).zfill(3)} {element['element_name']}: " + ", ".join(buffer_data[i][j]) + "\n"
            byte_offset += element['bytewidth']

        vb_merged += "\n"

    return vb_merged[:-1]


def output_results(frame_dump_folder, character, component_names, model_data, vb_merged, position_vb, current_part, texture_only, object_classifications, has_normalmap):
    # Note that this is not the same as the the distinction between components that is seen with the .fbx files
    # Characters can be split up in weird ways in the buffers (e.g. Kokomi has her hands in the "head" object)

    print(model_data, current_part)
    sorted_indexes = sorted(model_data[current_part].keys())
    count = 0
    for index in sorted_indexes:
        # Actually pretty rare to see more than three objects drawn on a single buffer, though I have seen four a few times
        # Now generalized to work with N objects, just repeats the last object with 2,3,4 etc.
        if count+1 > len(object_classifications):
            classification = f"{object_classifications[-1]}{count + 2 - len(object_classifications)}"
        else:
            classification = object_classifications[count]
        print(f"索引 {index} 的 {classification} 對象。")
        print(f"相關文件：{model_data[current_part][index]}")

        # The second object and above are named CharacterXClassification
        name_prefix = f"{character}"
        if component_names:
            name_prefix += component_names[current_part].replace(" ", "")
        elif current_part > 0:
            name_prefix += str(current_part + 1)
        name_prefix += classification

        if not texture_only:
            position_vb_hash = position_vb.split("=")[1].split("-")[0]
            with open(os.path.join(character, f"{name_prefix}-vb0={position_vb_hash}.txt"), "w") as f:
                f.write(vb_merged)

            ib_hash = model_data[current_part][index][0].split("=")[1].split("-")[0]
            shutil.copyfile(os.path.join(frame_dump_folder, model_data[current_part][index][0]),
                            os.path.join(character, f"{name_prefix}-ib={ib_hash}.txt"))

        if has_normalmap:
            shutil.copyfile(os.path.join(frame_dump_folder, model_data[current_part][index][1]),
                            os.path.join(character, f"{name_prefix}NormalMap.dds"))
        else:
            shutil.copyfile(os.path.join(frame_dump_folder, model_data[current_part][index][1]),
                            os.path.join(character, f"{name_prefix}Diffuse.dds"))
        if len(model_data[current_part][index]) > 2:
            if has_normalmap:
                shutil.copyfile(os.path.join(frame_dump_folder, model_data[current_part][index][2]),
                                os.path.join(character, f"{name_prefix}Diffuse.dds"))
            else:
                shutil.copyfile(os.path.join(frame_dump_folder, model_data[current_part][index][2]),
                                os.path.join(character, f"{name_prefix}LightMap.dds"))
        if len(model_data[current_part][index]) > 3:
            if has_normalmap:
                texture_hash = ""
                texture_type = "LightMap"
                shutil.copyfile(os.path.join(frame_dump_folder, model_data[current_part][index][3]),
                                os.path.join(character, f"{name_prefix}LightMap.dds"))
            else:
                texture_hash = model_data[current_part][index][3].split("-vs=")[0].split("=")[-1]
                extension, texture_type = identify_texture(frame_dump_folder, model_data[current_part][index][3])
                shutil.copyfile(os.path.join(frame_dump_folder, model_data[current_part][index][3]),
                                os.path.join(character, f"{name_prefix}{texture_type}{extension}"))
        if len(model_data[current_part][index]) > 4:
            texture_hash2 = model_data[current_part][index][4].split("-vs=")[0].split("=")[-1]
            if texture_hash2 != texture_hash:
                extension2, texture_type2 = identify_texture(frame_dump_folder, model_data[current_part][index][4])
                if texture_type2 == texture_type:
                    texture_type2 = "t3"
                shutil.copyfile(os.path.join(frame_dump_folder, model_data[current_part][index][4]),
                                os.path.join(character, f"{name_prefix}{texture_type2}{extension2}"))
        count += 1


# Gets the stride from the corresponding vb file
def get_stride(vb_file_path):
    with open(vb_file_path, "r") as f:
        return [x.split(": ")[1] for x in f.read().splitlines() if "stride: " in x][0]


# No easy way to figure out textures from names alone, so have to look at properties
def identify_texture(frame_dump_folder, filename):
    extension = os.path.splitext(filename)[1]
    if extension == ".jpg":
        texture_type = "ShadowRamp"
    elif os.stat(os.path.join(frame_dump_folder, filename)).st_size < 5000:
        texture_type = "DiffuseGuide"
    elif os.stat(os.path.join(frame_dump_folder, filename)).st_size < 100684:
        texture_type = "MetalMap"
    else:
        texture_type = "Shadow"

    return extension, texture_type


def stripped_string(val):
    return val.strip()


if __name__ == "__main__":
    main()
    input("按任意鍵結束程式。")
