a
<!--
V0.2.0
By lewis252310

-->

<style>
    /* body { background-color: #404040 !important }
    h1,h2,h3,h4,h5,h6,p { color: #FFF !important } */
    .code_block {
        background-color: #EEEEEE;
        padding: 10px;
        margin: 10px;
    }
    a.section {
        color: #00AA00;
    }
    .properties {
        color: #9F88FF;
    }
    .comments{
        color: #666666;
    }
    .value {
        color: #0066FF
    }
</style>

#### 前言
這是一個基於 GIMI 的 ini 檔案解析/教學/文檔
並且這是第一個版本，所以涵蓋範圍只有最基礎的語法。
並且可能需一些程式語言的基礎。
不過不用擔心，後續我會慢慢更新的，最終目標是能夠讓所有人讀懂。
最初使用中文撰寫，所以如果你閱讀的並不是中文版本，可能需要注意一下翻譯上造成的歧異問題。

---

### 注意！以下所述僅限 GIMI，並不適用於以外的範圍。

---

### .ini 結構簡述
由於 ini 不是本篇的重點，並且 ini 相關語法可以在網路上找到，
所以這邊只會用最簡短的方式告訴你如何看懂 ini。
底下這是個範例，來源是一個很普通的 mod。
![img](./ini_code_simple.png)
可以簡單分成三個部分。節、參數與註解。
其中節和參數無大小寫之分，但在 GIMI 裡節會以大駝峰風格進行編寫。

__**節 (section)**__
被`[]`框起來的部分就是**節**…的開頭。
因為節是一個代碼區域(Code Block)的概念，其範圍包括當前行到下一個**節**的上一行，或是文件末尾。

__**參數 (properties)**__
或是叫屬性。是節的子項目(至少到目前我都還沒有看過單獨存在的參數)。簡易的判斷方法是必定有一個`=`存在。

__**註釋 (comments)**__
又稱註解，從`;`開始，直到行結束。
這邊有一個點要注意，ini 只能註釋單獨行，也就是說把分號放在參數或節之後是不允許的。
```ini
; 單獨註釋整行，允許
[TextureOverrideA] ; 在節或參數之後註釋，不允許
hash = abcd1234 ; 其實可以看到在錯誤地方註釋的話註釋會是錯誤的顏色
```

ini 的簡單介紹就到這裡，基本上只要知道怎麼分辨節跟參數，會寫註釋就夠了。
如果還有興趣請自行[上網](https://wangchujiang.com/reference/docs/ini.html)找查或 [Wiki](https://en.wikipedia.org/wiki/INI_file)。
最後再重複一次，ini 無大小寫之分，但在 GIMI 中節的名稱是大駝峰風格。

---

現在可以來說說 GIMI 實際上會用到的各種東西了。我們就從 GIMI 的 ini 檔案中的各種保留字開始。

---

Here is a code example. Those that can be clicked on are words with their own meanings, and those that can't be clicked on are normal values.

<div class="code_block">
    [<a class="section" href="#override" title="Override">TextureOverrideLumainBody</a>]
    <br>
    <a class="properties" href="#hash" title="Hash">hash</a> = <span class="value" title="Normal value">afd36b46</span>
    <br>
    <a class="properties" herf="#match_first_index" title="Match first index">match_first_index</a> = <span class="value" title="Normal value">12800</span>
    <br>
    <a class="properties" href="#handling">handling</a> = <span class="value">skip</span>
    <br>
    <a class="properties" href="#ib">ib</a> = <a class="resource" href="#resource">ResourceLumainBodyIB</a>
    <br><br>
    [<a class="section" href="#resource">ResourceLumainBodyIB</a>]
    <br>
    <a class="properties" href="#type-resourse">type</a> = <span class="value">Buffer</span>
    <br>
    <a class="properties" href="#format">format</a> = <span class="value">DXGI_FORMAT_R32_UINT</span>
    <br>
    <a class="properties" href="#filename">filename</a> = <span class="value">LumainBody.ib</span>
</div>

---


### 語法樹
> 這裡是語法樹，修飾詞在下一節

[[\*Override\*]](#override)
├ [hash](#hash)
├ [handling](#handling)
├ [drawindexed](#drawindexed)
├ [match_first_index](#match_first_index)
├ [vb0, vb1, vb2, ...](#vbx)
├ [ib](#ib)
├ [ps-t0, ps-t1, ps-t2, ps-t3, ...](#ps-tx)
├ [filter_index](#filter_index)
├ [allow_duplicate_hash](#allow_duplicate_hash)
├ [match_priority](#match_priority)
├ [match_type](#match_type)
├ [match_width](#match_width)
├ [match_height](#match_height)
├ [match_msaa](#match_msaa)
├ [match_msaa_quality](#match_msaa_quality)
├ [match_usage](#match_usage)
├ [match_bind_flags](#match_bind_flags)
├ [match_cpu_access_flags](#match_cpu_access_flags)
├ [match_misc_flags](#match_misc_flags)
├ [match_byte_width](#match_byte_width)
├ [match_stride](#match_stride)
├ [match_mips](#match_mips)
├ [match_format](#match_format)
├ [match_depth](#match_depth)
└ [match_array](#match_array)

[[Resourse*]](#resource)
├ [type](#type-resourse)
├ [filename](#filename)
├ [format](#format)
├ [stride](#stride)
└ [data](#data)

[[CommandList*]](#commandlist)

[[Constants]](#constants)

[[Present]](#present)

[[Key*]](#key-section)
├ [key](#key-properties)
├ [type](#type-key)
└ [warp](#warp)

> 如果沒有在這裡找到你需要的，那可能是保留字或修飾詞。

---

### 修飾詞
> 這裡是修飾詞，語法樹在上一節

[post](#post)
[pre](#pre)
[global](#global)
[local](#local)
[persist](#persist)
[ref](#ref) <- 還不知道

---

### 保留字
> 這裡是參數保留字，

[if, endif, else if, else](#條件-condition)
[run](#run)

---

### 規則
> 這裡是一些通用規則

[變數 (variable)](#變數-variable)
[條件 (condition)](#條件-condition)
[錯誤訊息 (ERROR msg)](#錯誤訊息-error-msg)
[運算符 (Operators)](#運算符-operators)

---

## Override
 - > Attribute: 保留字 節 hash 觸發 偵聽
   > Parents
   > Childs: [hash]()


有紋理覆蓋(`TextureOverride`)與著色器覆蓋(`ShaderOverride`)兩種。
當螢幕上有對應的哈希值物件時便會觸發對應的 Override 節運作。
是 GIMI 的運作核心，是所有 Mod 的開始。
```ini
[*Override*]
[TextureOverrideLumainBody]
[ShaderOverridGroundHealthBar]
```

#### hash

[Override](#override)的參數之一。
告訴 GIMI 他需要注意哪個物件，並且發現時執行對應的動作。
```ini
[TextureOverrideLumainBody]
hash = afd36b46
```

#### handling

[Override](#override)的參數之一。
對指定物件的渲染操作，通常會使用 skip 來跳過渲染。
```ini
[TextureOverrideLumainPantsu]
handling = skip
```

#### drawindexed

告訴 GIMI 進行我們自己的繪製，而不是使用遊戲繪製。
通常會和 [handling](#handling) 一起使用。
```ini
[TextureOverrideLumainBody]
drawindexed = auto
```

#### draw
```ini
[TextureOverrideLumainBlend]
draw = 25600, 0
```

#### match_first_index

指定緩衝區的起始位置。有時候一個哈希可能包含不只一個物件，所以需要指定能正確加載資源。
```ini
[TextureOverrideLumainBody]
match_first_index = 25600
```

#### vbx
頂點緩衝區(vertex buffer)。通常會直接指向其他 [Resource](#resource) 節。
```ini
[TextureOverrideLumainBody]
vb0 = ResourceLumainPosition
```

#### ib
縮引緩衝區(index buffer)。通常會直接指向裝有 IB 的 [Resource](#resource) 節。
```ini
[TextureOverrideLumainBody]
vb0 = ResourceLumainBodyIB
```

#### ps-tx
紋理資源層。有幾種不同的類型，一般來說 t0 是紋理貼圖，t1 是光線貼圖，t2 是光澤貼圖， t3 是陰影貼圖。
```ini
[TextureOverrideLumainPantsu]
ps-t0 = ResourceLumainPantsuDiffuse
ps-t1 = ResourceLumainPantsuLightMap
ps-t2 = ResourceLumainPantsuMetalMap
ps-t3 = ResourceLumainPantsuShadowRamp

```

#### filter_index

宣告一個檢查值，定且能夠允許在其他地方進行檢查。
應該是會占用到 ps-t0，所以不確定倒底是不是一個好辦法。
<!-- 其實還是不是很確定，從 Bard 得到的結果是說可以禁用指定的過濾器 -->
```ini
[TextureOverrideLumainGlasses]
filter_index = 34
```

#### allow_duplicate_hash
ShaderOverride 參數。
控制允許覆蓋同樣 hash 與否。
可用值有：
 - true - 有重複時覆蓋
 - false - 有重複時不覆蓋
 - overrule - 強制覆蓋，好像是插件層級的覆蓋。
```ini
[ShaderOverrideLumainQEffect]
hash = 030dbce199e10697
allow_duplicate_hash = overrule
```

#### match_priority
TextureOverride 參數。
宣告覆蓋先後的順序權重。值越高則越優先。
GIMI 裡不怎麼會用到，唯一會用上的情況是用他來消除哈希相衝的問題，直接設定成 0 就好了。
```ini
[TextureOverrideLumainGlasses]
match_priority = 0
```

#### match_type
TextureOverride 參數。
代替 [hash](#hash)。當所選類型的任意物件被渲染時調用。
```ini
[TextureOverrideTexture2D]
match_type = Texture2D
```

#### match_width
TextureOverride 參數。
檢查並匹配紋理資源的寬度。
```ini
[TextureOverrideWidth1024]
match_width = 1024
```

#### match_height
TextureOverride 參數。
檢查並匹配紋理資源的高度。
```ini
[TextureOverrideHeight1024]
match_height = 1024
```

#### match_msaa
TextureOverride 參數。
按照 MSAA 過濾(我們不使用)。
```ini
[TextureOverrideMsaa]
match_msaa = 1
```

#### match_msaa_quality
TextureOverride 參數。
```ini
[TextureOverrideMsaaQuality]
match_msaa_quality = 1
```

#### match_usage
TextureOverride 參數。
這個設置沒有太大的意義，默認 DEFAULT。
更詳細的資訊：
https://learn.microsoft.com/en-us/windows/win32/api/d3d11/ne-d3d11-d3d11_usage
```ini
[TextureOverrideUsage]
match_usage = IMMUTABLE
```

#### match_bind_flags
TextureOverride 參數。
另一種過濾器。
在標誌前添加 `+` 或 `-` 來改變過濾運作。
如果沒有添加 `+` 或 `-` 則不使用該過濾器。
(我知道這說明有點模糊，之後會繼續詳細。)
```ini
[TextureOverrideAllBindFlags]
match_bind_flags = +VERTEX_BUFFER -INDEX_BUFFER CONSTANT_BUFFER SHADER_RESOURCE STREAM_OUTPUT RENDER_TARGET DEPTH_STENCIL UNORDERED_ACCESS DECODER VIDEO_ENCODER
```

#### match_cpu_access_flags
TextureOverride 參數。
另一種過濾器。
在標誌前添加 `+` 或 `-` 來改變過濾運作。
如果沒有添加 `+` 或 `-` 則不使用該過濾器。
(我知道這說明有點模糊，之後會繼續詳細。)
```ini
[TextureOverrideAllCPUAccessFlags]
match_cpu_access_flags = +READ -WRITE
```

#### match_misc_flags
TextureOverride 參數。
另一種過濾器。
在標誌前添加 `+` 或 `-` 來改變過濾運作。
如果沒有添加 `+` 或 `-` 則不使用該過濾器。
(我知道這說明有點模糊，之後會繼續詳細。)
```ini
[TextureOverrideAllMiscFlags]
match_misc_flags = GENERATE_MIPS SHARED TEXTURECUBE DRAWINDIRECT_ARGS BUFFER_ALLOW_RAW_VIEWS BUFFER_STRUCTURED RESOURCE_CLAMP SHARED_KEYEDMUTEX GDI_COMPATIBLE SHARED_NTHANDLE RESTRICTED_CONTENT RESTRICT_SHARED_RESOURCE RESTRICT_SHARED_RESOURCE_DRIVER GUARDED TILE_POOL TILED
```

#### match_byte_width
TextureOverride 參數。
匹配字節(byte)長度
```ini
[TextureOverrideByteWidth]
match_byte_width = res_width * res_height
```

#### match_stride
TextureOverride 參數。
某種跟跟緩衝器(Buffer)有關的東西。
(應該是跟 [stride](#stride) 有關的，字面意思則是匹配 stride 的值，需要進一步測試。)
```ini
[TextureOverrideStride]
match_stride = 40
```

#### match_mips
TextureOverride 參數。
```ini
[TextureOverrideMips]
match_mips = 1
```

#### match_format
TextureOverride 參數。
依照 [format](#format) 過濾。
對於修改沒有恆定 [hash](#hash) 的資源很有用。
DX 格式列表：
https://learn.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format
```ini
[TextureOverrideFormat]
match_format = R32G32B32A32_FLOAT
```

#### match_depth
TextureOverride 參數。
(應該是紋理的深度。)
```ini
[TextureOverrideDepth]
match_depth = 1
```

#### match_array
TextureOverride 參數。
(應該是紋理的某種資料陣列。)
```ini
[TextureOverrideArray]
match_array = 12
```

---

## Resource
 - > 保留字 節 資源

我不確定他是不是 GIMI 保留字之一，但因為帶有資源的節基本都是以`Resource`開頭，姑且也視為節保留字吧。
除了便於識別，也比較不會跟其他真正有特殊用途的節搞混。
通常用於儲存各種資源的位置。
```ini
[Resource*]
[ResourceLumainPantsu]
[ResourceMyRGBWeapon]
```

#### type (Resourse)
這的是 [Resourse](#resource) 下的設參數，而不是 [[Key]](#key-section) 下的參數。
宣告這個資源的類型，一般來說只會用到緩衝(Buffer)類型。
```ini
[ResourceLumainPantsuPosition]
type = Buffer
``` 

#### filename
 - > 保留字 餐數 資源

只出現在 [Resourse](#resource) 底下，使用相對路徑指向資源的儲存位置。
不清楚是否支持絕對路徑，但在這種可轉發數據資料中使用絕對路徑也沒有意義。
```ini
[ResourceLumainPantsu]
filename = .\pantsu0\LumainPantsu.dds
```

#### format
用於 IB 資源，單個縮引值的大小
```ini
[ResourceLumainBodyIB]
format = DXGI_FORMAT_R32_UINT
```

#### stride
用於 VB 資源，單個頂點總數據的字節大小
```ini
[ResourceLumainPantsu]
stride = 20
```

#### data
用於詳細日誌紀錄、用戶介面文本等
```ini
[ResourceLumainPantsu]
data = "Jsut a string."
```

---

## CommandList
 - > 保留字 節 運行

我不確定`CommandList`是不是保留字之一，因為理論上他就只是一個好幾條參數堆在一起的節，只有在有需要的時候才會呼叫。
不過其功能類似於 Function，所以我認為還是視為保留字會比較好。
```ini
[CommandList*]
[CommandListToggleLogic]
[CommandListCallTheAmbulance]
```
由於 `CommandList` 裡全都是進階的運算，所以沒有任何固定參數。
唯一會重複看到的就是各種[變數](#變數-variable)和[條件](#條件-condition)

---

## Constants
 - > 保留字 節 運行 變數

全域變數的初始化位置。
只要是全域變數(`global $var`)都需要在`Constants`節底下宣告，不然 GIMI 認不出你的變數。
只會在讀取 ini 時運行一次。[變數相關請戳我](#變數-variable)。
```ini
[Constants]
global $active = 0
```

---

## Present
 - > 保留字 節 運行

不斷重複執行的節。
這個節會在每一幀開始時運行一次。
通常會放入各種需要實時計算的代碼，例如按鍵切換外觀等...各種交互表現。
```ini
[Present]
post $active = 0
```
`Constants` 同 [CommandList](#commandlist) 是用於各種運算的區域，所以也沒有固定參數，但一般來說不會在這裡直接指向 [Resource](#resource)，而是先指向 CommandList 再去呼叫 Resource


---

## Key (section)
 - > 保留字 節 偵聽 觸發

定義 GIMI 要偵測那些按鍵的狀況。
按下去之後執行設定好的運作。
下面這個例子定義了一個 Q 鍵，[類型](#type-key)則是`toggle`
```ini
[KeyHelp]
key = q
type = toggle
```

#### key (properties)
用於 [Key](#key-section) 節，指定要監聽哪個按鍵。
在[這裡](https://learn.microsoft.com/zh-tw/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN)可以找到所有可用的按鍵類型。
```
[KeyHelp]
key = q
```

#### type (Key)

這的是 [[Key]](#key-section) 下的設參數，而不是 [Resourse](#resource) 下的參數。
宣告 [key](#key-properties) 的類型。有四種可用值，分別是默認、cycle、hold 及 toggle。
1. 默認：單純運行。沒有寫 type 時默認的類型，單純運行所寫配置。
2. cycle：循環。按順序遍歷所寫列表，可藉由 [warp](#warp) 控制是否頭尾相連循環。
3. hold：長按。長按時持續觸發，可以應用在一些需要長按的技能上。
4. toggle：開關。單純的開關，如果上一次觸發是 1，那麼下一次觸發就是 0。
```ini
[KeyK]
key = k
type = cycle
$swapvar = 0, 1, 2, 3
```

#### warp
控制 key - cycle 類型時是否允許頭尾相連循環。
預設值為 True。
```ini
[KeyK]
key = k
warp = false
type = cycle
$swapvar = 0, 1, 2, 3
```

---

## 修飾詞

#### post
 - > 修飾詞 參數 流程控制

指定對應參數在幀 ***結束時*** 運算，例如設定幀開始時間。
```ini
post $triggerDate = time
```

#### pre
 - > 修飾詞 參數 流程控制

指定對應參數在幀 ***開始時*** 運算，例如計算 [Present](#present) 的運行次數。
```ini
pre $auxTime = $auxTime + 1
```

#### global
 - > 修飾詞 參數 流程控制 變數

宣告**全域**變數時必要的修飾詞。 [變數規則請戳我](#變數-variable)
另外注意，全域變數只會在 [Constants](#constants) 宣告。
```ini
[Constants]
global $a_global_var = 1
```

#### local
 - > 修飾詞 參數 流程控制 變數

宣告**區域**變數時必要的修飾詞。 [變數規則請戳我](#變數-variable)
區域變數可以在任何需要計算的地方隨時宣告，但不確定 GIMI 對於區域變數的回收機制是如何，至少到目前 local 變數見的不多。
```ini
[AnySection]
local $i = 0
```

#### persist
 - > 修飾詞 參數 變數

宣告變數**持久化**時必要的修飾詞。 [變數規則請戳我](#變數-variable)
只會出現在全域變數(global)的宣告上，宣告後這個變數就會持久儲存在`d3dx_user.ini`裡，只有使用`Ctrl + Alt + F10`之後才會重製。
```ini
[Constants]
global persist $a_persist_var = 1
```

#### ref
暫無更多詳細訊息…
應該是類似於指針或指向的作用，
```ini
pre ResourceHelp = ref ResourceHelpFull
```

#### run

宣告要執行的節。
常見的就是指向 [CommandList](#commandlist) 去做更進一步的運算。
```ini
[KeyChangeColor]
run = CommandListLumainChangePanTsuColor
```

---

#### 變數 (variable)
 - > 變數 規則

GIMI 中只有以`$`符號開頭才會識別為變數，而如果在一些應該是變數的位置卻沒有`$`符號，那個就是[保留字](#保留字)。
```ini
$last_date = time
; $last_date 是我們設定的變數，time 則是 GIMI 的保留字。
```

#### 條件 (condition)
 - > 條件 規則

GIMI 中的條件控制保留字有`if`，`else if`，`else`以及`endif`
用`if`開始條件塊，用`endif`結束條件塊。支持巢狀。
如果你是程式語言新手，請從其他程式語言的條件語法來熟悉條件控制，本篇將不過多敘述。
```ini
if time == $lest_date + 10.0
    run = CommandListA
else if time == $lest_date + 15.0
    run = CommandListB
else
    run = CommandListC
endif
```

#### 錯誤訊息 (ERROR msg)

暫無更多詳細訊息…

#### 運算符 (Operators)

這只是一個在 GIMI 允許使用的運算符列表，不包含任何使用教程。

| Operators | Name           | Note                      |
| --------- | -------------- | ------------------------- |
| +         | Addition       |                           |
| -         | Subtraction    |                           |
| *         | Multiplication |                           |
| /         | Division       |                           |
| %         | Modulus        |                           |
| =         | Assignment     |                           |
| ==        | Equal          |                           |
| !=        | Not equal      |                           |
| !==       |                | not sure what dif with != |