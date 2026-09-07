#!/usr/bin/env python3
"""从 raw/capabilities.json 生成 openapi/openapi.yaml（Bridge API v0.49，72 路由）.

用法: python3 scripts/build-openapi.py
输入: raw/capabilities.json, raw/status_auth.json
输出: openapi/openapi.yaml

META 管 tag/summary/语义/confirm；PARAMS 管 path/query 参数；
BODIES 管请求体 JSON Schema。三者都以运行时 GET /guide 为准，
capabilities 只提供路由清单与 requiresMax。
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAP = ROOT / "raw" / "capabilities.json"
STATUS = ROOT / "raw" / "status_auth.json"
OUT = ROOT / "openapi" / "openapi.yaml"

META = {
    # (method, path) -> (tag, summary, description, confirm)
    ("GET", "/status"): ("System", "服务状态（免鉴权）", "唯一免 token 端点。返回 bridgeApiVersion/routeCount/apiFingerprint/guideVersion/guideHash/authorized。连通性判据只看它，不要用 lsof。", False),
    ("GET", "/capabilities"): ("System", "运行时能力清单", "返回实际注册的全部路由 {method,path,requiresMax}、presets/anchorModes/accessPolicy 等机器可读契约。能力边界以它为准。", False),
    ("GET", "/guide"): ("System", "运行时操作规程 Markdown", "用现有 Bearer token 读取，与已加载 Skill 的 guideVersion/guideHash 比对，不一致则以返回为准。只读刷新，不轮换 token。", False),
    ("GET", "/context"): ("System", "用户此刻上下文", "只读。返回 studySet/currentPage/documents(含focused)/selectedNotes/focusedNote。currentPage.page 为 PDF 页序；blank 页用换算后的真实页。available:false 按 reason 回退，不重试。", False),
    ("GET", "/install"): ("Setup", "安装脚本（一次性码）", "GET /bridge/v1/install?code=xxx。code 10 分钟有效、只能用一次。成功返回 shell 安装脚本（写 token + 装 Skill）；失败 403 返回无效/过期提示脚本。", False),
    ("POST", "/install/code"): ("Setup", "安装码相关", "安装辅助路由，无 confirm 门，不轮换 token、不写 Skill 文件。具体语义以运行时 GET /guide 为准；刷新规程只读 GET /guide。", False),
    ("POST", "/mcp"): ("Setup", "MCP 通道", "MCP 客户端接入点：claude mcp add --transport http marginnote http://127.0.0.1:{port}/bridge/v1/mcp --header \"Authorization: Bearer $TOKEN\"。工具仅 mn_guide（规程）与 mn_call（{method,path,body} 转发）。GET /mcp 未实现（501），以 POST 通道为准。", False),
    ("GET", "/library/study-sets"): ("Library", "列出学习集", "返回学习集列表。不含复习卡组（卡组走 GET /decks）。支持 ?query= 过滤。", False),
    ("POST", "/library/study-sets"): ("Library", "新建空学习集", "Body {title, confirm:true}。返回 {topicid, isStudySet}，必须校验 isStudySet:true。空集含一张与集同名的根卡。", True),
    ("POST", "/library/documents/upload"): ("Library", "上传文档进资料库", "Body 为文件原始字节，参数走 query：?filename=必填&folder=可选&topicid=可选&confirm=1。filename 决定 MN 内名字；folder 为文档根相对路径；topicid 顺手绑集（以 addedToStudySet 为准）；confirm=1 必填（确认前已传完一遍，直接带最省流量）。同名不覆盖。无按本机路径导入。", True),
    ("POST", "/library/documents/{id}/delete"): ("Library", "删除资料库文档（干净撤销）", "仅无卡片锚定该书时执行，否则 409 DOCUMENT_IN_USE。虚拟文档拒删。无回收站，删完回读自证（partial:true 即半删）。导入时自动建的空文档笔记本会留下。", True),
    ("GET", "/library/folders"): ("Library", "列文档文件夹", "?path=&depth=。\"\" 为根。文件夹与学习集/标签互不影响，挪文件夹不破坏卡片。", False),
    ("GET", "/study-sets/{id}/documents"): ("StudySets", "列学习集文档", "返回该集引用的文档（含 sourceState normal/missing_file、主文档信息）。", False),
    ("POST", "/study-sets/{id}/documents"): ("StudySets", "给学习集加文档", "Body {bookmd5, confirm:true}。文档须已在资料库。首加成主文档（becameMainDocument），再加为 addedToBooklist；重复加幂等 alreadyPresent。", True),
    ("POST", "/study-sets/{id}/documents/{id}/delete"): ("StudySets", "从学习集移除文档", "对齐 App「从学习集中移除」。文档留库，但该书有锚卡片会失去回源（startpage 清空）。先不带 confirm 打一次看 details.notesLosingSource，告知用户后再 confirm。服务端自动打快照（preRemoveSnapshotId）。", True),
    ("POST", "/study-sets/{id}/open"): ("StudySets", "打开学习集", "Body {bookmd5?}。不给即主文档；文档须本机有文件（否则 422 DOCUMENT_FILE_MISSING）。可临时打开非本集KERSEY（tempOpen:true）。异步跳转，事后 GET /context 对账。不改数据，无需 confirm。", False),
    ("GET", "/study-sets/{id}/tree"): ("StudySets", "脑图树", "返回扁平 nodes[]（{noteid,parent,depth,childCount,…}），父子靠 parent 拼，非嵌套 children。subMapId 为归属标签（住在哪张子脑图里）。title 超 64 截断；完整内容走 batch-get。?root= 读单张子脑图。", False),
    ("GET", "/study-sets/{id}/sub-maps"): ("StudySets", "列子脑图", "每项 {noteid(根卡),title,cardCount,parentPath,depth}，顺序同 App。depth>0 为嵌套。", False),
    ("GET", "/study-sets/{id}/snapshots"): ("StudySets", "列学习集快照", "版本点列表。复用语义注意：内容无变化时复用既有版本点。", False),
    ("POST", "/study-sets/{id}/snapshots"): ("StudySets", "打学习集快照", "Body {description}（不加 Agent: 前缀，服务端加）。无 confirm 门，发即执行。无变化时复用并回 created:false + warnings；旧服务端无 created 字段时须回读列表核对条数。批量写前必打。", False),
    ("POST", "/study-sets/{id}/delete"): ("StudySets", "删除学习集", "最重写动词。Body {expectedTitle(须与库中完全一致), confirm:true, keepHighlights?=true, keepSnapshotHistory?=true}。默认隐藏卡片+保留划线+自动打快照（preDeleteSnapshotId）。彻底清才传 false（不可恢复）。卡组删除走同一端点（keepHighlights:false 才真删干净）。", True),
    ("GET", "/study-sets/{id}/notebooks"): ("StudySets", "学习集引用的文档笔记本", "返回该集引用了哪些文档笔记本。", False),
    ("GET", "/study-sets/{id}/hashtags"): ("StudySets", "学习集标签树", "返回实际存储 hashtags[]、派生扁平 nodes[]、嵌套 tree[]。directCardCount 仅直存；cardCount 含后代；derived:true 为推导层。", False),
    ("GET", "/study-sets/{id}/note-palette"): ("StudySets", "学习集摘录色板", "返回恰好 16 项 {colorIndex(0-based),baseColor,displayColor(hex+rgba)}。source 为 default/study-set。拆书 [style:] 与 metadata 选色前必读，禁止硬编码颜色名。", False),
    ("POST", "/study-sets/{id}/mindmap-print/preview"): ("StudySets", "脑图打印预览计划", "Body {mode:keepStructure|classic|cardFlow, densityValue?, rootNoteId?}。keepStructure 默认逐级打印；classic/densityValue=1 走旧兼容；cardFlow 密集卡片流。返回 schema mn.mindMapPrintPlan.v0，含 pageCountEstimate/pages[]/exportOptions/planFingerprint。分页以 native 为准，CLI 不自算。", False),
    ("POST", "/study-sets/{id}/mindmap-print/export"): ("StudySets", "按计划导出脑图 PDF", "推荐 Body {plan:<preview 保存的计划>, fileName?}。复用 pages[]/visibleDepth/visibleNoteIds。输出到外部导出根 MindMapExports。只建文件不改数据，无需 confirm。与文档导出共享 EXPORT_BUSY（429）。", False),
    ("GET", "/documents/{id}/outline"): ("Documents", "文档目录", "返回 segments（字段名是 segments，不是 entries）+ hasToc + pageCount（pageCount 在离屏打开失败时可能为 0，以 pages 二分探末页为准）。", False),
    ("GET", "/documents/{id}/pages"): ("Documents", "读文档页文本", "?start=&end=（≤60 页/次）。start/end 与 prepare segments 同为 PDF 页序（第一页=1）。&blocks=1 变块探针（返回块清单 {index,text,label}，较慢，探 1-2 页）。读正文用它，不绕 prepare。", False),
    ("GET", "/documents/{id}/pages/{index}/parts"): ("Documents", "页视觉注释面", "?studySet= 仅调旧 blank map 解析优先级，仍合并该文档所在全部 topic（topicFilteringApplied:false）。返回 parts[]（可读图像清单）与 blanks[]（逻辑留白，contentIds 指向图像）。mapBacked:false 为恢复项。", False),
    ("GET", "/documents/{id}/pages/{index}/content/{id}"): ("Documents", "取页手写/留白合成图", "?maxEdge=64–4096 &studySet=。先读 parts 再按需取图，不逐页盲渲染。", False),
    ("GET", "/documents/{id}/toc-candidates"): ("Documents", "AI 目录标题候选", "?start=&end=（≤60 页/次硬上限）。每页渲染+OCR+版面模型，扫描件约 3s/页；服务端 45s 预算，超限返回部分 + truncated:true/nextStart/hint，按 hint 从 nextStart 续扫。并发上限 2（与 pages 共享），超限 429 SCAN_BUSY。返回 {page,text,height,anchor}（anchor 原样回带；height 为字号代理）。", False),
    ("POST", "/documents/{id}/toc"): ("Documents", "写 AI 目录 / 切回原始目录", "写：{entries:[{title,page,level(0-7),anchor?}], confirm:true}，页码须递增，越级静默钳（adjustedLevels）。落 AI 目录位，原目录无损。回退：{useOriginal:true,confirm:true} 切回原始；{useAI:true,confirm:true} 切回 AI。快照救不了目录。真 dry-run（不带 confirm 回 422 + details.wouldWrite）。", True),
    ("POST", "/documents/{id}/locate"): ("Documents", "按原文找位置", "Body {text(逐字照抄), page(必填), navigate?}。返回 {found,page,matchedText,algorithm,score}，须核对 matchedText。no_match 多为改写原文；page_unreadable 为页不可读。navigate:true 仅滚动（不高亮），跨文档不跳（navigated:false + different_document_open）。", False),
    ("POST", "/documents/{id}/export"): ("Documents", "导出文档扁平 PDF", "Body {topicid(必填，定标注层), selectedPageNos(真实 PDF 页，省略=全书，空数组拒), includeRelatedBlankPages?=true}。留白页由 native 隐式带上，不计数、不入 selectedPageNos（拒绝 66000+ 虚拟页）。输出到外部导出根 DocumentExports。只建文件不改数据。若已有导出在跑 429 EXPORT_BUSY。", False),
    ("GET", "/documents/{id}/sync-status"): ("Documents", "单文档同步对账", "[?verifyHash=1]（默认不算 hash；verifyHash 会全文件扫描，大 PDF 慢）。以 state 为准：database_reference_without_document_mapping/waiting_for_icloud_download 且 hasLearningData判学习数据先行；library_record_only 勿称笔记已到；available_local_only 先看 expectedByCurrentSettings；verified_mismatch/icloud_error/mapped_but_not_materialized 才列异常。databaseQueryErrors 存在时为部分证据；全失败回 SYNC_DIAGNOSTIC_QUERY_FAILED。", False),
    ("POST", "/notes/batch-get"): ("Notes", "批量读卡", "Body {noteIds:[…]} ≤200/次。返回 texts[]（对象数组 {index,text,excerpt,noteid,kind}，index 0=卡正文，1..N=子笔记；稀疏，空留白 kind:blank 也返回）、parts[]（视觉顺序全量，含 contentPath/mimeType/ocrText；0.42 起图片遮挡项带 occlusion 与 occlusionBaseContentPath）、metadata{colorIndex,fillIndex}、hashtags/hashtagPaths。texts 为空先看 parts。", False),
    ("POST", "/notes/hashtags"): ("Notes", "写卡片 hashtag", "Body {noteIds(≤200), operation:add|remove|replace, hashtags(完整叶路径，如 #医学/心血管/心衰), includeDescendants?(仅 remove), confirm:true}。禁止用 text 接口伪造标签（422 HASHTAG_ROUTE_REQUIRED）。replace 空数组=清空（须展示获同意）。整批一撤销组，persisted:true 才成功。", True),
    ("POST", "/notes/metadata"): ("Notes", "改卡片/摘录样式", "Body {noteIds(≤200), patch:{colorIndex 0..15?, fillIndex -1..2?}, confirm:true}。选色前读 note-palette。整批一撤销组，独立 context 回读一致才 persisted:true。", True),
    ("POST", "/notes/move"): ("Notes", "移动卡片", "Body {noteIds:[…], targetParentNoteId} 或批量 {moves:[{noteIds,targetParentNoteId}], confirm:true}，合计 ≤50/次，整批一撤销组。同集改父子，不调兄弟顺序/坐标（Bridge 无此能力）。调用前展示逐卡方案获同意。", True),
    ("POST", "/notes/copy"): ("Notes", "复制卡片分支", "Body {noteIds,targetParentNoteId,mode:reference|clone,confirm:true} 或批量 copies[]。复制所选根整棵分支（快照，不随源树后续调整同步）；祖先后代同选时后代 covered_by_selected_ancestor 跳过；≤50 根；目标须为已存在普通脑图卡；源不能是隐藏/复习卡。可跨集（源文档按规则加入目标集）。真 dry-run（422 + wouldCopy）。persisted:true 才成功。", True),
    ("POST", "/notes/delete"): ("Notes", "删除卡片", "Body {noteIds(≤50，同集), confirm:true}，整批一撤销组。只删点名卡，子卡接到祖父（grandparent）或升顶层重排（topLevel）。合并子笔记随卡消失；虚拟卡断引用；闪卡复制体级联。回收站默认关，先打快照。逐卡展示标题+子卡去向获同意。outcome deleted/hidden 如实转告。真 dry-run（422 + wouldDelete/cards[]/totalCascadeDeleted/cascadesIntoStudySets）。", True),
    ("POST", "/notes/fold"): ("Notes", "折叠/展开", "Body {noteIds(≤200), folded:true|false, confirm:true}，整批一撤销组。最轻写动词，只改视图。叶子无折叠语义（skipped no_children）。脑图开着时可能需重进才见。", True),
    ("GET", "/notes/{id}/content/{id}"): ("Notes", "读卡片二进制项", "?maxEdge=64–4096（默认 2048）&layers=composite|base(0.42 起，base 省旧 mask 位图，按 occlusionBaseContentPath 用)。摘录/插图/手写回合成图；音视频回原始二进制。MCP mn_call 中图片以 image 内容返回。", False),
    ("GET", "/notes/{id}/render"): ("Notes", "整卡渲染", "?format=png|pdf &width=320–1200。标题+文字+摘录图+插图+独立脑图手写的合成长图/PDF。超 3600 万像素拒绝。用于看整卡/视觉校对，不代批量文本读取。代价最高，按需用。", False),
    ("POST", "/notes/{id}/image-occlusions"): ("Notes", "原生图片挖空", "给已存在图片/PDF 摘录笔记增/替原生遮罩（highlight_pic.maskRects）。Body {coordinateSpace:normalized, operation:add|replace, masks:[{rect:{x,y,w,h},group?,flags?,isText?}](1..200), expectedSourceFingerprint, confirm?, expectedMaskFingerprint?}。须先读 batch-get，用 occlusionBaseContentPath 底图出候选并预览。真 dry-run（422 CONFIRM_REQUIRED + sourceFingerprint/maskFingerprint/映射数/旧复习卡警告）；指纹变了 409 IMAGE_SOURCE_CHANGED/OCCLUSION_CHANGED。persisted:true 才成功；已有复习卡为快照，不自动改写。", True),
    ("POST", "/notes/{id}/title"): ("Notes", "改标题", "Body {text, expectedPrefix(当前值前 32 字，为空传 \"\"), confirm:true, markdown?}。改写/删除前展示原文→改后获同意；编辑会话前打快照。exam-general×block 下答案卡标题可能被归一，submit 后对 receipt，须保留的用此接口补回（不受归一限制）。", True),
    ("POST", "/notes/{id}/text"): ("Notes", "改正文", "Body 同改标题。对 kind:blank 的 texts[].noteid 用同一端点。改正文前判摘录卡（texts[].excerpt 任一 true，或 sourceAnchor.hasExcerpt；勿用 sourceAnchor.page 判 block 包）。摘录卡改文致文字与原书脱钩（回源不受影响），须告知用户。", True),
    ("POST", "/notes/{id}/comments"): ("Notes", "追加评论", "Body {text, confirm:true}。整条为 marginnote4app://note/… URL 时成真双链（生成式整理回链旧卡用此）。", True),
    ("POST", "/notes/{id}/comments/{index}"): ("Notes", "改写评论", "Body {text, expectedPrefix(前 32 字), confirm:true}。index 取 batch-get texts[].index 的 1..N（0 为卡正文，传 0 422）。须先读最新，409 COMMENT_CHANGED 重读再来。", True),
    ("POST", "/notes/{id}/comments/{index}/delete"): ("Notes", "删除评论", "Body {expectedPrefix, confirm:true}。index 语义同改写。", True),
    ("POST", "/notes/{id}/merge-branch"): ("Notes", "合并分支", "Body {confirm:true, recursive?}。默认只合直接子卡；recursive:true 合整棵子树。dry-run 列 willMerge[]，先念给用户听。合不了的原样留树（notMergedCount）；摘要卡/子脑图根卡自动跳过（skipped）。整组可撤销。注意这是合并（对方消失），不是链接。", True),
    ("POST", "/notes/{id}/fold-into-sub-map"): ("Notes", "折成子脑图 / 展回", "Body {confirm:true} 折叠（须有子节点，否则 422 NO_CHILDREN）；{undo:true, confirm:true} 展回。", True),
    ("POST", "/notes/{id}/focus"): ("Notes", "定位到卡", "Body {topicid?}。多集引用同一卡时用 topicid 指定。走 MN URL scheme，与书架点击同路。会抢屏，仅用户要求时用。异步，事后 /context 对账。无 confirm。", False),
    ("GET", "/decks"): ("Decks", "列复习卡组", "返回 {deckId,title,cardCount,lastModifiedAt}。不列学习集（集走 library/study-sets），id 不通用。", False),
    ("POST", "/decks"): ("Decks", "新建复习卡组", "Body {title, confirm:true}。返回 {deckId, isDeck}，须校验 isDeck:true。", True),
    ("GET", "/decks/{id}/cards"): ("Decks", "列复习卡", "返回 {cardNoteId,sourceNoteId,sourceAlive,title}。sourceAlive:false=原卡已删/隐藏，背面空白。", False),
    ("POST", "/decks/{id}/cards"): ("Decks", "加复习卡", "Body {cards:[{sourceNoteId(必填), question?, questionContentId?, title?}], confirm:true} ≤50/次，整批一撤销组。question/questionContentId 互斥；都不给走 autoQuestionIndex。{{挖空}} 写 question。同一源卡重复加为更新并重排到期（updatedExisting）。组员 id 归一到宿主（resolvedNoteId）。删单张复习卡用 POST /notes/delete（单向联动：删复习卡不影响源卡，删源卡级联删复习卡）。", True),
    ("POST", "/decks/{id}/open"): ("Decks", "打开复习卡组", "与 study-sets open 语义类似，id 不通用（传错 422 NOT_A_DECK/IS_A_DECK）。异步，事后 /context 对账。", False),
    ("POST", "/bundles/prepare"): ("Bundles", "准备拆书任务包", "Body {topicid, bookmd5, segments[{startPage,endPage,title}](PDF 页序，非连续可，实际页数≤60), preset(book-breakdown|source-structure|exam-general|dictionary), anchorMode(page_text|block), title?, cardStyle{defaultFillIndex -1..2}?, async?}。>~10 页必 async:true（202 {jobId,bundleId,bundlePath,state:preparing} + 轮询 GET /bundles；参数错同步 404/422）。单飞（429 PREPARE_BUSY 看 details.runningJob/retryAfterSeconds）。exam-general 必须配 block（含 role 标注），否则静默退化；错配 0.18+ 回 warnings（停下改组合重 prepare）。同步小包阻塞到完工（curl ≥300s）。", False),
    ("GET", "/bundles"): ("Bundles", "列任务包/作业", "?origin=bridge(只看自建) &since=(磁盘包按目录创建时间，作业按开始时间)。字段 bundleId/jobId/bundlePath/topicid/bookmd5/createdAt/state(preparing|prepared|imported|failed|cancelled)+progress/version/rootNoteId/running。state 缺字段按缺席处理。jobId 非 null 不等于本会话活作业。", False),
    ("GET", "/bundles/{id}/files"): ("Bundles", "列包文件 / 取单文件", "?path= 取单个原始内容（curl -o 落盘）。跨设备读包靠它。", False),
    ("POST", "/bundles/{id}/submit"): ("Bundles", "提交导入（commit）", "Body {targetParentNoteId?, withBlank?, excerptMode?:child|link, resultMarkdown?(仅跨设备)}。无 confirm 门，发即真执行。返回 {rootNoteId, version, preImportSnapshotId(存好，USER_EDITS_PRESENT 时带 force:true 才覆盖), receipt, parsed{headings,importedCards,wikilinks,excerptsTotal,excerptsAnchored,failedExcerpts[]}, warnings, excerptStatsTruncated?, blankInsertion?}。headings≠importedCards 即丢卡；excerptsAnchored 不等即有未定位摘录（no_match 多为改写原文）。并发重复提交 409 SUBMIT_IN_FLIGHT。", False),
    ("POST", "/bundles/{id}/focus"): ("Bundles", "聚焦导入结果", "无 confirm 门。异步，事后 /context 对账。", False),
    ("POST", "/bundles/{id}/discard"): ("Bundles", "删除任务包 / 取消作业", "幂等。已导入卡片不受影响。对 preparing 即取消（cancelledJob 非 null 为真取消）。刚 discard 立刻重 prepare 易 429（等取消检查点）。同步 prepare 被并发 discard 则 409 PREPARE_CANCELLED。500 DISCARD_FAILED 为目录删不掉（残留按 details.bundleId 手工清）。", False),
    ("POST", "/snapshots/{id}/restore"): ("Snapshots", "回退快照", "Body {confirm:true(, force:true 若 USER_EDITS_PRESENT 且用户确认覆盖)}。回退整集到过去，自动先打回退前保护点（protectionSnapshotId）。目标集正开着回 409 STUDY_SET_IN_USE（切走再试）。文档目录不在快照覆盖范围。真 dry-run（422 + wouldRestoreToVersion/快照时间/说明/卡数）。", True),
    ("GET", "/search"): ("Search", "全库搜索", "?q=&scope=all|notes|studysets|documents。返回卡/集/文档三类命中。无列全库文档端点，找书用 scope=documents 拿 bookmd5。响应带 scanned/truncated；truncated:true=窗口没够到，加词重搜。新卡约 10s 索引延迟。", False),
    ("GET", "/sync/legacy/status"): ("Sync", "旧同步诊断快照", "返回 cloudKit/documents/diagnostic（无正文/文档名/账号/record id）。errorCount 为历史诊断数；suspended 看 suspensionNeedsAttention（false 可为正常增量暂停）；当前周期错误看 suspensionErrorCount。", False),
    ("GET", "/sync/legacy/events"): ("Sync", "旧同步增量事件", "?afterSequence=N&limit=50（1..200）。用 lastSequence 续取；hasMore 续取；historyTruncated=窗口外/缺口（勿称完整）；cursorAdvancedPastGap=已推游标防死循环；cursorAhead=换 channel/设备（重置游标）。", False),
    ("POST", "/sync/legacy/recheck"): ("Sync", "旧同步安全重核", "Body {database?=true, documents?=true}。复用 checkSync+PopulateShelf，不 reset/删/覆盖；但可能应用待处理远端变更。accepted 仅受理，记 operationId/startSequence 后读 events/status。", False),
    ("POST", "/sync/legacy/inventory"): ("Sync", "旧同步只读盘点", "分页观察 private zone 顶层存在性。Query 最终一致 + 非快照，结果非权威（observed≠完整；possible_mismatch 须按 record ID 核验）。observe-only，不上传/删；独立低优先级非蜂窝队列；关 Bridge 即关。会耗配额。", False),
    ("GET", "/ui-state"): ("UIState", "读界面状态", "工作场景书签读端。键多自解释；{_jsonvalueType} 包装值原样带回。", False),
    ("POST", "/ui-state/apply"): ("UIState", "应用界面状态", "Body {state:{…}}（差量补丁；缺键保持）。无 confirm 门，发即提交。异步（~1.5s），queued:true 仅提交，~2s 后 GET 对账。accepted/conditional（依赖缺失静默跳过）/rejected（play 与 doclayerid:new 拒收）。缺 topicid 注入当前集；无开集则拒绝。theme/panelratio 写全局偏好；immersive 弄脏同步；researchurl 加载任意 URL。", False),
}

TAG_ORDER = ["System", "Setup", "Library", "StudySets", "Documents", "Notes", "Decks", "Bundles", "Snapshots", "Search", "Sync", "UIState"]

# path 模板变量说明（按端点逐个指定；未指定的用通用“路径 id”）
PATH_DESCS = {
    ("GET", "/study-sets/{id}/documents"): {"id": "学习集 topicid"},
    ("POST", "/study-sets/{id}/documents"): {"id": "学习集 topicid"},
    ("POST", "/study-sets/{id}/documents/{id}/delete"): {"id": "学习集 topicid（两处 id 含义不同，见名）"},
    ("POST", "/study-sets/{id}/open"): {"id": "学习集 topicid"},
    ("GET", "/study-sets/{id}/tree"): {"id": "学习集 topicid"},
    ("GET", "/study-sets/{id}/sub-maps"): {"id": "学习集 topicid"},
    ("GET", "/study-sets/{id}/snapshots"): {"id": "学习集 topicid"},
    ("POST", "/study-sets/{id}/snapshots"): {"id": "学习集 topicid"},
    ("POST", "/study-sets/{id}/delete"): {"id": "学习集 topicid（卡组删除走同一端点时为 deckId）"},
    ("GET", "/study-sets/{id}/notebooks"): {"id": "学习集 topicid"},
    ("GET", "/study-sets/{id}/hashtags"): {"id": "学习集 topicid"},
    ("GET", "/study-sets/{id}/note-palette"): {"id": "学习集 topicid"},
    ("POST", "/study-sets/{id}/mindmap-print/preview"): {"id": "学习集 topicid"},
    ("POST", "/study-sets/{id}/mindmap-print/export"): {"id": "学习集 topicid"},
    ("GET", "/documents/{id}/outline"): {"id": "文档 bookmd5"},
    ("GET", "/documents/{id}/pages"): {"id": "文档 bookmd5"},
    ("GET", "/documents/{id}/pages/{index}/parts"): {"id": "文档 bookmd5", "index": "PDF 页序（第一页=1，勿传留白虚拟页号）"},
    ("GET", "/documents/{id}/pages/{index}/content/{id}"): {"id": "文档 bookmd5", "index": "PDF 页序"},
    ("GET", "/documents/{id}/toc-candidates"): {"id": "文档 bookmd5"},
    ("POST", "/documents/{id}/toc"): {"id": "文档 bookmd5"},
    ("POST", "/documents/{id}/locate"): {"id": "文档 bookmd5"},
    ("POST", "/documents/{id}/export"): {"id": "文档 bookmd5"},
    ("GET", "/documents/{id}/sync-status"): {"id": "文档 bookmd5"},
    ("POST", "/library/documents/{id}/delete"): {"id": "文档 bookmd5"},
    ("GET", "/notes/{id}/content/{id}"): {"id": "卡片 noteid"},
    ("GET", "/notes/{id}/render"): {"id": "卡片 noteid"},
    ("POST", "/notes/{id}/image-occlusions"): {"id": "图片/PDF 摘录笔记 noteid"},
    ("POST", "/notes/{id}/title"): {"id": "卡片 noteid"},
    ("POST", "/notes/{id}/text"): {"id": "卡片 noteid"},
    ("POST", "/notes/{id}/comments"): {"id": "卡片 noteid"},
    ("POST", "/notes/{id}/comments/{index}"): {"id": "卡片 noteid", "index": "评论序号 1..N（0 为卡正文，传 0 会 422）"},
    ("POST", "/notes/{id}/comments/{index}/delete"): {"id": "卡片 noteid", "index": "评论序号 1..N"},
    ("POST", "/notes/{id}/merge-branch"): {"id": "卡片 noteid"},
    ("POST", "/notes/{id}/fold-into-sub-map"): {"id": "卡片 noteid"},
    ("POST", "/notes/{id}/focus"): {"id": "卡片 noteid"},
    ("GET", "/decks/{id}/cards"): {"id": "复习卡组 deckId（与 topicid 不通用）"},
    ("POST", "/decks/{id}/cards"): {"id": "复习卡组 deckId"},
    ("POST", "/decks/{id}/open"): {"id": "复习卡组 deckId"},
    ("GET", "/bundles/{id}/files"): {"id": "任务包 bundleId"},
    ("POST", "/bundles/{id}/submit"): {"id": "任务包 bundleId"},
    ("POST", "/bundles/{id}/focus"): {"id": "任务包 bundleId"},
    ("POST", "/bundles/{id}/discard"): {"id": "任务包 bundleId"},
    ("POST", "/snapshots/{id}/restore"): {"id": "快照 id（打点/导入/删除响应里的 snapshotId）"},
}

# query 参数：(method, path) -> [{name, required, type, desc, enum?}]
QUERY = {
    ("GET", "/install"): [
        {"name": "code", "required": True, "type": "string", "desc": "一次性安装码，10 分钟有效、只能用一次"},
    ],
    ("GET", "/library/study-sets"): [
        {"name": "query", "required": False, "type": "string", "desc": "按标题过滤学习集"},
    ],
    ("GET", "/decks"): [
        {"name": "query", "required": False, "type": "string", "desc": "按标题过滤复习卡组"},
    ],
    ("GET", "/library/folders"): [
        {"name": "path", "required": False, "type": "string", "desc": "文档根相对路径，空字符串为根"},
        {"name": "depth", "required": False, "type": "integer", "desc": "列举深度"},
    ],
    ("GET", "/study-sets/{id}/tree"): [
        {"name": "root", "required": False, "type": "string", "desc": "子脑图根卡 noteid，只读该张子脑图"},
    ],
    ("GET", "/documents/{id}/pages"): [
        {"name": "start", "required": False, "type": "integer", "desc": "起始 PDF 页（第一页=1）"},
        {"name": "end", "required": False, "type": "integer", "desc": "结束 PDF 页，单次 ≤60 页"},
        {"name": "blocks", "required": False, "type": "integer", "desc": "=1 变块探针，返回块清单（较慢，探 1-2 页）"},
    ],
    ("GET", "/documents/{id}/pages/{index}/parts"): [
        {"name": "studySet", "required": False, "type": "string", "desc": "仅调旧 blank map 解析优先级，仍合并全部 topic"},
    ],
    ("GET", "/documents/{id}/pages/{index}/content/{id}"): [
        {"name": "maxEdge", "required": False, "type": "integer", "desc": "最长边 64–4096，默认按 parts 取图即可"},
        {"name": "studySet", "required": False, "type": "string", "desc": "旧 blank map 解析优先级"},
    ],
    ("GET", "/documents/{id}/toc-candidates"): [
        {"name": "start", "required": False, "type": "integer", "desc": "起始页"},
        {"name": "end", "required": False, "type": "integer", "desc": "结束页，单次 ≤60 页硬上限"},
    ],
    ("GET", "/documents/{id}/sync-status"): [
        {"name": "verifyHash", "required": False, "type": "integer", "desc": "=1 计算内容 hash（全文件扫描，大 PDF 慢）"},
    ],
    ("GET", "/notes/{id}/content/{id}"): [
        {"name": "maxEdge", "required": False, "type": "integer", "desc": "最长边 64–4096，默认 2048"},
        {"name": "layers", "required": False, "type": "string", "desc": "composite（默认）|base（0.42 起，省旧 mask 位图）", "enum": ["composite", "base"]},
    ],
    ("GET", "/notes/{id}/render"): [
        {"name": "format", "required": False, "type": "string", "desc": "png|pdf", "enum": ["png", "pdf"]},
        {"name": "width", "required": False, "type": "integer", "desc": "320–1200"},
    ],
    ("GET", "/bundles"): [
        {"name": "origin", "required": False, "type": "string", "desc": "=bridge 只看自建任务包"},
        {"name": "since", "required": False, "type": "string", "desc": "按时间过滤（磁盘包按目录创建时间，作业按开始时间）"},
    ],
    ("GET", "/bundles/{id}/files"): [
        {"name": "path", "required": False, "type": "string", "desc": "包内文件路径，如 source.json；不传列文件清单"},
    ],
    ("GET", "/search"): [
        {"name": "q", "required": True, "type": "string", "desc": "关键词；truncated:true 时加词缩小范围重搜"},
        {"name": "scope", "required": False, "type": "string", "desc": "all|notes|studysets|documents", "enum": ["all", "notes", "studysets", "documents"]},
    ],
    ("GET", "/sync/legacy/events"): [
        {"name": "afterSequence", "required": False, "type": "integer", "desc": "从该 sequence 之后取"},
        {"name": "limit", "required": False, "type": "integer", "desc": "1..200，默认 50"},
    ],
    ("POST", "/library/documents/upload"): [
        {"name": "filename", "required": True, "type": "string", "desc": "纯文件名，决定 MN 内名字；同名不覆盖"},
        {"name": "folder", "required": False, "type": "string", "desc": "文档根相对路径；不传落到用户上次浏览文件夹"},
        {"name": "topicid", "required": False, "type": "string", "desc": "顺手绑定的学习集，以 addedToStudySet 为准"},
        {"name": "confirm", "required": True, "type": "integer", "desc": "=1 确认写入（文件确认前已传完，直接带最省流量）"},
    ],
}

# 请求体：(method, path) -> {"mime": str, "required": [..], "props": {name: (type, desc, extra?)}, "desc": str}
# extra 可含 enum/items/$ref 内联；想保持生成器简单，复杂结构用 type+desc 表达。
def _p(t, d, **kw):
    return {"type": t, "desc": d, **kw}

BODIES = {
    ("POST", "/library/study-sets"): {
        "required": ["title", "confirm"],
        "props": {
            "title": _p("string", "新学习集标题，调用前告知用户"),
            "confirm": _p("boolean", "确认建集"),
        },
    },
    ("POST", "/library/documents/{id}/delete"): {
        "required": ["confirm"],
        "props": {"confirm": _p("boolean", "确认删除；仅干净撤销（无锚定卡片）才执行")},
    },
    ("POST", "/study-sets/{id}/documents"): {
        "required": ["bookmd5", "confirm"],
        "props": {
            "bookmd5": _p("string", "已在资料库的文档"),
            "confirm": _p("boolean", "确认加入"),
        },
    },
    ("POST", "/study-sets/{id}/documents/{id}/delete"): {
        "required": ["confirm"],
        "props": {"confirm": _p("boolean", "先不带打一次看 notesLosingSource，告知用户后再带")},
    },
    ("POST", "/study-sets/{id}/open"): {
        "required": [],
        "props": {"bookmd5": _p("string", "可选，不给即主文档；须本机有文件")},
    },
    ("POST", "/study-sets/{id}/snapshots"): {
        "required": [],
        "props": {"description": _p("string", "版本点说明，不加 Agent: 前缀")},
    },
    ("POST", "/study-sets/{id}/delete"): {
        "required": ["expectedTitle", "confirm"],
        "props": {
            "expectedTitle": _p("string", "须与库中现值完全一致，否则 409 TITLE_MISMATCH"),
            "confirm": _p("boolean", "确认删除（最重写动词）"),
            "keepHighlights": _p("boolean", "默认 true（隐藏卡+保留划线）；false 才真删干净"),
            "keepSnapshotHistory": _p("boolean", "默认 true（自动打快照）；false 连快照历史一起清"),
        },
    },
    ("POST", "/study-sets/{id}/mindmap-print/preview"): {
        "required": ["mode"],
        "props": {
            "mode": _p("string", "keepStructure|classic|cardFlow", enum=["keepStructure", "classic", "cardFlow"]),
            "densityValue": _p("number", "0..1，classic 兼容值 0.995"),
            "rootNoteId": _p("string", "可选分支根卡，只打该分支"),
        },
    },
    ("POST", "/study-sets/{id}/mindmap-print/export"): {
        "required": [],
        "props": {
            "plan": _p("object", "preview 返回并保存的完整计划（含 pages/visibleDepth/visibleNoteIds）"),
            "fileName": _p("string", "可选输出文件名"),
        },
    },
    ("POST", "/documents/{id}/toc"): {
        "required": ["confirm"],
        "props": {
            "entries": _p("array", "目录条目 [{title,page,level(0-7),anchor?}]，页码须递增", items={"type": "object"}),
            "confirm": _p("boolean", "确认写入（多集可见，快照救不了）"),
            "useOriginal": _p("boolean", "true=切回原始目录（唯一回退口）"),
            "useAI": _p("boolean", "true=切回 AI 目录"),
        },
    },
    ("POST", "/documents/{id}/locate"): {
        "required": ["text", "page"],
        "props": {
            "text": _p("string", "逐字照抄的原文"),
            "page": _p("integer", "必填，PDF 页序"),
            "navigate": _p("boolean", "true 仅滚动不高亮；跨文档不跳"),
        },
    },
    ("POST", "/documents/{id}/export"): {
        "required": ["topicid"],
        "props": {
            "topicid": _p("string", "必填，定标注层"),
            "selectedPageNos": _p("array", "真实 PDF 页数组；省略=全书；空数组被拒；勿传留白虚拟页", items={"type": "integer"}),
            "includeRelatedBlankPages": _p("boolean", "默认 true，留白由 native 隐式带上"),
        },
    },
    ("POST", "/notes/batch-get"): {
        "required": ["noteIds"],
        "props": {"noteIds": _p("array", "卡片 id 数组，≤200/次", items={"type": "string"})},
    },
    ("POST", "/notes/hashtags"): {
        "required": ["noteIds", "operation", "hashtags", "confirm"],
        "props": {
            "noteIds": _p("array", "≤200", items={"type": "string"}),
            "operation": _p("string", "add|remove|replace", enum=["add", "remove", "replace"]),
            "hashtags": _p("array", "完整叶路径数组；replace 空数组=清空（须同意）", items={"type": "string"}),
            "includeDescendants": _p("boolean", "仅 remove 有效，连同子标签一起删"),
            "confirm": _p("boolean", "确认写入"),
        },
    },
    ("POST", "/notes/metadata"): {
        "required": ["noteIds", "patch", "confirm"],
        "props": {
            "noteIds": _p("array", "≤200", items={"type": "string"}),
            "patch": _p("object", "{colorIndex 0..15?, fillIndex -1..2?}，选色前读 note-palette"),
            "confirm": _p("boolean", "确认修改"),
        },
    },
    ("POST", "/notes/move"): {
        "required": ["confirm"],
        "props": {
            "noteIds": _p("array", "待移卡片（简单形态）", items={"type": "string"}),
            "targetParentNoteId": _p("string", "目标父卡（简单形态）"),
            "moves": _p("array", "批量形态 [{noteIds,targetParentNoteId}]，合计 ≤50/次", items={"type": "object"}),
            "confirm": _p("boolean", "调用前展示逐卡方案获同意"),
        },
    },
    ("POST", "/notes/copy"): {
        "required": ["confirm"],
        "props": {
            "noteIds": _p("array", "所选根卡（简单形态），≤50 根", items={"type": "string"}),
            "targetParentNoteId": _p("string", "目标父卡（简单形态，须已存在普通脑图卡）"),
            "mode": _p("string", "reference（同步）|clone（独立）", enum=["reference", "clone"]),
            "copies": _p("array", "批量形态 [{noteIds,targetParentNoteId,mode}]", items={"type": "object"}),
            "confirm": _p("boolean", "先展示源卡/模式→目标分组获同意"),
        },
    },
    ("POST", "/notes/delete"): {
        "required": ["noteIds", "confirm"],
        "props": {
            "noteIds": _p("array", "≤50，同集；只删点名卡", items={"type": "string"}),
            "confirm": _p("boolean", "展示标题+子卡去向获同意；先打快照"),
        },
    },
    ("POST", "/notes/fold"): {
        "required": ["noteIds", "folded", "confirm"],
        "props": {
            "noteIds": _p("array", "≤200", items={"type": "string"}),
            "folded": _p("boolean", "true 折叠 / false 展开"),
            "confirm": _p("boolean", "确认"),
        },
    },
    ("POST", "/notes/{id}/image-occlusions"): {
        "required": ["masks", "expectedSourceFingerprint"],
        "props": {
            "coordinateSpace": _p("string", "固定 normalized（左上角归一化）"),
            "operation": _p("string", "add|replace", enum=["add", "replace"]),
            "masks": _p("array", "1..200 [{rect:{x,y,w,h},group?,flags?,isText?}]", items={"type": "object"}),
            "expectedSourceFingerprint": _p("string", "dry-run 与确认都必带"),
            "expectedMaskFingerprint": _p("string", "确认写入必带（dry-run 返回）"),
            "confirm": _p("boolean", "确认写入；不带为真 dry-run"),
        },
    },
    ("POST", "/notes/{id}/title"): {
        "required": ["text", "confirm"],
        "props": {
            "text": _p("string", "新标题"),
            "expectedPrefix": _p("string", "当前值前 32 字，为空传 \"\""),
            "confirm": _p("boolean", "展示原文→改后获同意"),
            "markdown": _p("boolean", "标题是否按 Markdown 解析"),
        },
    },
    ("POST", "/notes/{id}/text"): {
        "required": ["text", "confirm"],
        "props": {
            "text": _p("string", "新正文；摘录卡改文须先告知脱钩后果"),
            "expectedPrefix": _p("string", "当前值前 32 字，为空传 \"\""),
            "confirm": _p("boolean", "确认修改"),
            "markdown": _p("boolean", "是否按 Markdown 解析"),
        },
    },
    ("POST", "/notes/{id}/comments"): {
        "required": ["text", "confirm"],
        "props": {
            "text": _p("string", "评论内容；整条 note URL 成真双链"),
            "confirm": _p("boolean", "确认追加"),
        },
    },
    ("POST", "/notes/{id}/comments/{index}"): {
        "required": ["text", "confirm"],
        "props": {
            "text": _p("string", "新评论内容"),
            "expectedPrefix": _p("string", "当前评论前 32 字"),
            "confirm": _p("boolean", "确认改写"),
        },
    },
    ("POST", "/notes/{id}/comments/{index}/delete"): {
        "required": ["confirm"],
        "props": {
            "expectedPrefix": _p("string", "当前评论前 32 字"),
            "confirm": _p("boolean", "确认删除"),
        },
    },
    ("POST", "/notes/{id}/merge-branch"): {
        "required": ["confirm"],
        "props": {
            "confirm": _p("boolean", "先把 willMerge[] 念给用户听再带"),
            "recursive": _p("boolean", "true 合整棵子树，默认只合直接子卡"),
        },
    },
    ("POST", "/notes/{id}/fold-into-sub-map"): {
        "required": ["confirm"],
        "props": {
            "confirm": _p("boolean", "确认折叠/展回"),
            "undo": _p("boolean", "true 展回普通分支"),
        },
    },
    ("POST", "/notes/{id}/focus"): {
        "required": [],
        "props": {"topicid": _p("string", "多集引用同一卡时指定在哪个集里打开")},
    },
    ("POST", "/decks"): {
        "required": ["title", "confirm"],
        "props": {
            "title": _p("string", "新卡组标题"),
            "confirm": _p("boolean", "确认新建；校验 isDeck:true"),
        },
    },
    ("POST", "/decks/{id}/cards"): {
        "required": ["cards", "confirm"],
        "props": {
            "cards": _p("array", "≤50 [{sourceNoteId(必填), question?, questionContentId?, title?}]，question 与 questionContentId 互斥", items={"type": "object"}),
            "confirm": _p("boolean", "确认加入"),
        },
    },
    ("POST", "/bundles/prepare"): {
        "required": ["topicid", "bookmd5", "segments"],
        "props": {
            "topicid": _p("string", "目标学习集"),
            "bookmd5": _p("string", "源文档"),
            "segments": _p("array", "[{startPage,endPage,title}] PDF 页序；可非连续；实际页数 ≤60", items={"type": "object"}),
            "preset": _p("string", "book-breakdown|source-structure|exam-general|dictionary", enum=["book-breakdown", "source-structure", "exam-general", "dictionary"]),
            "anchorMode": _p("string", "page_text|block", enum=["page_text", "block"]),
            "title": _p("string", "任务说明"),
            "cardStyle": _p("object", "{defaultFillIndex -1..2}"),
            "async": _p("boolean", ">~10 页必 true，走作业模式"),
        },
    },
    ("POST", "/bundles/{id}/submit"): {
        "required": [],
        "props": {
            "targetParentNoteId": _p("string", "可选落点父卡，先 tree 选好"),
            "withBlank": _p("boolean", "每条成功摘录后插标准空留白"),
            "excerptMode": _p("string", "child（默认）|link", enum=["child", "link"]),
            "resultMarkdown": _p("string", "仅跨设备：result.md 全文内联交回"),
        },
    },
    ("POST", "/snapshots/{id}/restore"): {
        "required": ["confirm"],
        "props": {
            "confirm": _p("boolean", "展示版本时间/说明获同意；不带为真 dry-run"),
            "force": _p("boolean", "USER_EDITS_PRESENT 且用户确认覆盖才带"),
        },
    },
    ("POST", "/sync/legacy/recheck"): {
        "required": [],
        "props": {
            "database": _p("boolean", "默认 true，核对 CloudKit 数据库通道"),
            "documents": _p("boolean", "默认 true，核对文档通道"),
        },
    },
    ("POST", "/ui-state/apply"): {
        "required": ["state"],
        "props": {"state": _p("object", "差量补丁；缺键保持现状")},
    },
    ("POST", "/mcp"): {
        "required": [],
        "props": {},
        "raw_desc": "MCP JSON-RPC 通道，工具仅 mn_guide 与 mn_call（{method,path,body} 转发到同一批端点）。",
    },
    ("POST", "/install/code"): {
        "required": [],
        "props": {},
        "raw_desc": "安装辅助路由，具体语义以运行时 GET /guide 为准；不轮换 token。",
    },
    ("POST", "/decks/{id}/open"): {
        "required": [],
        "props": {},
        "raw_desc": "打开复习卡组（空 body 即可）；id 与学习集不通用。",
    },
    ("POST", "/bundles/{id}/focus"): {
        "required": [],
        "props": {},
        "raw_desc": "聚焦导入结果（空 body 即可）；异步，事后 /context 对账。",
    },
    ("POST", "/bundles/{id}/discard"): {
        "required": [],
        "props": {},
        "raw_desc": "删包/取消作业（空 body 即可）；幂等，已导入卡片不受影响。",
    },
    ("POST", "/sync/legacy/inventory"): {
        "required": [],
        "props": {},
        "raw_desc": "只读盘点触发端（空 body 即可）；observe-only，不上传/删。",
    },
}


def yaml_escape(s):
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return s


def q(s):
    return '"%s"' % yaml_escape(str(s))


def emit_schema(obj, indent):
    """把 python 结构打成 YAML 行（字符串一律双引号，避免解析歧义）。"""
    lines = []
    pad = " " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.extend(emit_schema(v, indent + 2))
            else:
                lines.append(f"{pad}{k}: {q(v)}")
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(emit_schema(v, indent + 2))
            else:
                lines.append(f"{pad}- {q(v)}")
    else:
        lines.append(f"{pad}{q(obj)}")
    return lines


def prop_schema(p):
    s = {"type": p["type"]}
    if "enum" in p:
        s["enum"] = p["enum"]
    if "items" in p:
        s["items"] = p["items"]
    s["description"] = p["desc"]
    return s


def main():
    cap = json.loads(CAP.read_text(encoding="utf-8"))
    routes = cap.get("routes", [])
    out_lines = []
    out_lines.append("openapi: 3.1.0")
    out_lines.append("info:")
    out_lines.append("  title: MarginNote Agent Bridge HTTP API")
    out_lines.append("  version: 0.49.0")
    out_lines.append("  description: >-")
    out_lines.append("    MarginNote 4 本地 Agent Bridge（loopback HTTP，默认 127.0.0.1:42340）的完整 HTTP 接口。")
    out_lines.append("    Base URL 为 http://127.0.0.1:{port}/bridge/v1，端口每次现查（42340 起扫 20 个）。")
    out_lines.append("    除 GET /status 外一律 Bearer 鉴权；写能力另需 MarginNote Max（以 requiresMax 为准）。")
    out_lines.append("    本文件由 raw/capabilities.json 生成（72 路由），语义细节以运行时 GET /guide 为准。")
    out_lines.append("servers:")
    out_lines.append("  - url: http://127.0.0.1:42340/bridge/v1")
    out_lines.append("    description: 本机默认（端口现查，见发现流程）")
    out_lines.append("security:")
    out_lines.append("  - bearerAuth: []")
    out_lines.append("paths:")
    grouped = {}
    for r in routes:
        key = (r["method"], r["path"])
        grouped[key] = r
    # 按 path 分组（同一 path 的多个 method 合并到同一个 path key 下，避免 YAML 重复键）
    by_path: dict = {}
    for (method, path), r in grouped.items():
        by_path.setdefault(path, []).append((method, r))
    # 按 TAG_ORDER 输出（取该 path 第一个 method 的 tag 排序）
    def path_sort_key(path):
        methods = by_path[path]
        tags = [META.get((m, path), ("Other", "", "", False))[0] for m, _ in methods]
        best = min(TAG_ORDER.index(t) if t in TAG_ORDER else 99 for t in tags)
        return (best, path)
    for path in sorted(by_path.keys(), key=path_sort_key):
        # 同一 path 下按 GET 优先排序，输出稳定
        methods = sorted(by_path[path], key=lambda mr: (0 if mr[0] == "GET" else 1, mr[0]))
        out_lines.append(f"  {path}:")
        for method, r in methods:
            tag, summary, desc, confirm = META.get((method, path), ("Other", path, "", False))
            requires_max = r.get("requiresMax", False)
            out_lines.append(f"    {method.lower()}:")
            out_lines.append(f'      operationId: "{method.lower()}-{path.strip("/").replace("/", "-").replace("{", "").replace("}", "")}"')
            out_lines.append(f'      summary: "{yaml_escape(summary)}"')
            out_lines.append(f'      description: "{yaml_escape(desc)}"')
            out_lines.append("      tags:")
            out_lines.append(f"        - {tag}")
            out_lines.append("      x-requires-max: " + ("true" if requires_max else "false"))
            out_lines.append("      x-requires-confirm: " + ("true" if confirm else "false"))
            if method == "GET" and path == "/status":
                out_lines.append("      security: []")
            # path 参数（模板变量逐个出；delete 双 id 处做区分命名展示）
            path_vars = re.findall(r"\{(\w+)\}", path)
            if path_vars:
                descs = PATH_DESCS.get((method, path), {})
                out_lines.append("      parameters:")
                seen = set()
                for v in path_vars:
                    if v in seen:
                        continue
                    seen.add(v)
                    d = descs.get(v, "路径 id（见描述）")
                    out_lines.append(f"        - name: {v}")
                    out_lines.append("          in: path")
                    out_lines.append("          required: true")
                    out_lines.append("          schema:")
                    out_lines.append("            type: string")
                    out_lines.append(f'          description: "{yaml_escape(d)}"')
            # query 参数
            for qp in QUERY.get((method, path), []):
                if not path_vars:
                    out_lines.append("      parameters:")
                    path_vars = ["_q"]
                out_lines.append(f"        - name: {qp['name']}")
                out_lines.append(f"          in: query")
                out_lines.append("          required: " + ("true" if qp["required"] else "false"))
                out_lines.append("          schema:")
                out_lines.append(f"            type: {qp['type']}")
                if "enum" in qp:
                    out_lines.append("            enum:")
                    for e in qp["enum"]:
                        out_lines.append(f'              - "{yaml_escape(e)}"')
                out_lines.append(f'          description: "{yaml_escape(qp["desc"])}"')
            # 请求体
            body = BODIES.get((method, path))
            if body is not None:
                if (method, path) == ("POST", "/library/documents/upload"):
                    pass  # 下面单独处理二进制体
                else:
                    out_lines.append("      requestBody:")
                    out_lines.append("        content:")
                    out_lines.append("          application/json:")
                    out_lines.append("            schema:")
                    if body.get("props"):
                        schema = {
                            "type": "object",
                            "required": body.get("required", []),
                            "properties": {k: prop_schema(v) for k, v in body["props"].items()},
                        }
                        if body.get("raw_desc"):
                            schema["description"] = body["raw_desc"]
                        out_lines.extend(emit_schema(schema, 14))
                    else:
                        out_lines.append("              type: object")
                        if body.get("raw_desc"):
                            out_lines.append(f'              description: "{yaml_escape(body["raw_desc"])}"')
            if (method, path) == ("POST", "/library/documents/upload"):
                out_lines.append("      requestBody:")
                out_lines.append("        required: true")
                out_lines.append("        content:")
                out_lines.append("          application/octet-stream:")
                out_lines.append("            schema:")
                out_lines.append("              type: string")
                out_lines.append("              format: binary")
                out_lines.append('              description: "文件原始字节；参数走 query（filename/folder/topicid/confirm）"')
            out_lines.append("      responses:")
            out_lines.append("        '200':")
            out_lines.append('          description: 成功（具体 schema 见 docs/reference 对应章节与运行时 /guide）')
            out_lines.append("        '401':")
            out_lines.append('          description: 令牌缺失/无效（UNAUTHORIZED）。TCP 通说明 Bridge 活着，换 token 重装。')
            out_lines.append("        '403':")
            out_lines.append('          description: FORBIDDEN_ORIGIN（带了 Origin 头，去掉重试）或 MAX_REQUIRED（需订阅，该写请求勿重试）或跨设备 APPROVAL_DENIED。')
            out_lines.append("        '422':")
            out_lines.append('          description: 参数/前置校验失败，或 confirm 门（CONFIRM_REQUIRED；六个重动词为真 dry-run，details 含已验事实）。')
    out_lines.append("components:")
    out_lines.append("  securitySchemes:")
    out_lines.append("    bearerAuth:")
    out_lines.append("      type: http")
    out_lines.append("      scheme: bearer")
    out_lines.append("      description: 安装脚本写入 ~/.config/mn-bridge/token，或环境变量 MN_BRIDGE_TOKEN。不要带 Origin 头。")
    out_lines.append("  schemas:")
    out_lines.append("    ApiError:")
    out_lines.append("      type: object")
    out_lines.append("      required: [error]")
    out_lines.append("      properties:")
    out_lines.append("        error:")
    out_lines.append("          type: object")
    out_lines.append("          properties:")
    out_lines.append("            code: {type: string, description: UNAUTHORIZED/FORBIDDEN_ORIGIN/MAX_REQUIRED/CONFIRM_REQUIRED 等}")
    out_lines.append("            message: {type: string}")
    out_lines.append("            retryable: {type: boolean}")
    out_lines.append("        bridgeApiVersion: {type: string, example: '0.49'}")
    out_lines.append("x-bridge:")
    out_lines.append(f"  bridgeApiVersion: {cap.get('bridgeApiVersion', '0.49')}")
    out_lines.append(f"  routeCount: {cap.get('routeCount', len(routes))}")
    out_lines.append(f"  apiFingerprint: {cap.get('apiFingerprint', '')}")
    out_lines.append(f"  guideVersion: {cap.get('guideVersion', '')}")
    out_lines.append(f"  guideHash: {cap.get('guideHash', '')}")
    out_lines.append(f"  presets: {json.dumps(cap.get('presets', []), ensure_ascii=False)}")
    out_lines.append(f"  anchorModes: {json.dumps(cap.get('anchorModes', []), ensure_ascii=False)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(routes)} routes)")


if __name__ == "__main__":
    main()
