# 第 6 讲实践篇：能力 seam 的作答与判定

本篇记录[第 6 讲讲义](lecture-6-capability-seam.md)五道小测的作答与判定。讲义只留题目，批改放在这里。

| 文件 | 作用 |
|---|---|
| [mini-harness/lecture-6/seam_core.py](../../mini-harness/lecture-6/seam_core.py) | 最小能力 seam。上下文与服务键、约定、两个 Provider、只认服务键的 Consumer、约定类型断言。 |
| [mini-harness/lecture-6/demo.py](../../mini-harness/lecture-6/demo.py) | 四个场景对应讲义四条动手任务，输出服务键装配、重复注册拒绝、换实现不改 Consumer、约定断言与反例。 |

两个文件只用标准库，离线运行。命令是 `cd mini-harness/lecture-6 && python3 demo.py`。

## 小测批改

### 第 1 题：三种变化与耦合后果

**题目。** 一项可替换能力涉及哪三种变化？把它们放在一个包里会出什么问题？

**正确答案。** 三种变化是约定、实现和消费方 API。约定指能力是什么、对外承诺什么行为。实现指这件事具体怎么跑。消费方 API 指模型看到的工具 schema 和插件调用的入口。放在一个包里会让发布时间绑在一起，换执行实现会带动面向模型的 schema 变动，即使约定本身没变。

**当时的回答。** 约定，这项能力是什么，对外承诺什么行为，比如命令执行要能跑前台命令、能拿后台句柄、能读有界输出。实现，这件事具体怎么跑，用本机子进程跑还是放进沙箱跑还是发到远程跑。消费方 API，模型看到的工具 schema 以及插件调用的入口，比如模型调用 bash 工具时填什么参数。把三件事放在一个包里，它们的发布时间就被绑在一起，换一个执行实现，模型看到的工具 schema 也跟着变动，尽管面向模型的约定根本没变。

**判定。** 正确。三种变化和耦合后果都答全，与讲义一致。本题为原文复述，内容无误。

### 第 2 题：Definition 为什么是 Service

**题目。** Service Definition 为什么必须是 Cordis `Service`，不能是 TypeScript `interface`？

**正确答案。** 因为它必须能拥有一个 `ctx.<key>` 服务键，`interface` 是编译期类型，拿不到服务键。它可以是抽象类，也可以是具体的注册表服务。

**当时的回答。** Service Definition 是 Cordis 的 Service，不是 TypeScript 的 interface。它可以是抽象类，也可以是具体的注册表服务。约束是必须能拥有一个 `ctx.<key>` 服务键，interface 做不到这件事。

**判定。** 正确。抓住了唯一硬约束，即 interface 拿不到服务键。本题为原文复述。

### 第 3 题：shell 三件套的角色与替换前提

**题目。** shell seam 里三个角色分别是哪个包？Consumer 凭什么能在换实现时一行不改？

**正确答案。** Service Definition 是 `dsh-shell`，声明 `ctx.shell` 并导出 `ShellExecutor` 等词汇类型。Service Provider 是 `dsh-bash-local` 和 `dsh-bash-sandbox`，都注册到 `ctx.shell`。Consumer 是 `dsh-tool-bash`，定义 `bash` 工具。Consumer 能一行不改，是因为它只注入 `shell` 这个服务键，全程不 import `LocalBashExecutor`，依赖落在约定上而非具体实现上。

**当时的回答。** 三个角色分在三个包里。Service Definition 是 dsh-shell，声明 Context 上有 shell 这个键，导出 ShellExecutor、ShellRunResult、ShellProcess 等词汇类型，核心是抽象类 ShellExecutor extends Service，构造函数用 super(ctx, 'shell') 挂到那个键上，一个 context 只装一个实现，装第二个会在加载期报错。Service Provider 是 dsh-bash-local，定义 LocalBashExecutor extends ShellExecutor，在 POSIX 上用 bash -c 进程跑命令，兄弟包 dsh-bash-sandbox 依据同一约定实现沙箱版，两者可互换。Consumer 是 dsh-tool-bash，面向模型的 bash 工具，声明 inject 包含 tools、shell、systemPrompt 等键，执行时用 ctx.shell.execute(spec) 拿结果，注入的是 shell 这个键，从头到尾不 import LocalBashExecutor，这正是换实现不动工具的前提。profile 层恰好选择一个执行器实现，同时挂两个会加载期失败，选择权在部署方。

**判定。** 正确。三个包名准确，替换前提答到点子上，即注入 `shell` 键且不 import 具体实现。本题为原文复述。

### 第 4 题：单一实现时该不该拆

**题目。** 一个能力只有一个实现时，该不该拆成三个包？给出判断标准和理由。

**正确答案。** 不该。判断标准是角色独立演进时才分开，确实属于同一关注点时可以合并。不要预防性拆分，一种实现加一个消费者就保持一个包，等第二个实现真的出现再拆。理由是拆三个包会多出三份 `package.json`、`tsconfig`、README 和注入接线。LLM 能力就是合并的例子，它把 Definition 和 Consumer 合进 `dsh-llm`。

**当时的回答。** 分工有代价，拆三个包就多三份 package.json、tsconfig、README 和注入接线。笔记给出的规则是角色独立演进时才分开，确实属于同一个关注点时可以合并。LLM 能力是合并的例子，把 Service Definition 和 Consumer 合进 dsh-llm，因为 Consumer 就是 agent loop 本身，不是一个可替换的 schema 接口，各家模型服务作为 Service Provider 包接进来。笔记特别提醒不要预防性地拆分，一种实现加一个消费者就保持一个包，等第二个出现再拆。还有一个易混点，Cordis 的 @cordisjs/plugin-capability 不是这里的机制，那是权限安全服务，用具名权限加继承，针对会话做检测。

**判定。** 正确。判断标准、理由和「一个实现时保持一个包」的结论都在。末尾关于 `@cordisjs/plugin-capability` 的区分是讲义里的相邻内容，本题未问，答到不算错。本题为原文复述。

### 第 5 题：平台取舍与场景应用

**题目。** 平台取舍题。你的 mini-harness 要接本地命令和沙箱命令两种执行器，工具 schema 只有一份。你会怎么切这几个角色，代价是什么？

**正确答案。** 场景里已经有两种实现，满足拆分条件，应该现在就切。切法是 Definition 为挂 `shell` 键的执行器抽象类，Provider 为本地与沙箱两个实现分别注册，Consumer 为那份唯一 schema 的工具，只注入 `shell` 键，换实现时不动 schema。代价有两层。多出三份包结构和接线成本。一个 context 只能装一个执行器，要在部署期做出选择。

**当时的回答。** 按照建议对命令执行、模型接入这类明显会换后端的能力保留 seam。判断标准沿用笔记那条，不要预防性拆分，等第二个实现真的出现再切。

**判定。** 部分正确。保留 seam 的方向对，但三处不到位。

第一，场景判断套错。题目给定本地和沙箱两种执行器都在，按「等第二个实现出现再切」的标准，第二个已经出现，此刻就该切，答成继续等是把原则当口号套用，没有核对题设条件。

第二，没答「怎么切这几个角色」。应落到 Definition、Provider 和 Consumer 的具体切法，以及 Consumer 只注入服务键这一点。

第三，没答「代价是什么」。应说出包结构与接线成本，以及一个 context 只能装一个实现带来的部署期选择。

## 总评

五题中四题内容正确，但均为讲义原文复述，检验的是记忆而非理解。第五题是唯一需要独立应用的开放题，暴露了应用层面的缺口。原则记住了，落到具体场景时没有核对条件，也没有给出切法和代价。下一轮自测建议脱稿作答，尤其是开放题。

## 动手：跑通四个场景

四个场景对应讲义的四条动手任务。下面是 `python3 demo.py` 的实际输出。

### 场景 1：服务键与约定

```
==============================================================
场景 1：Service Definition 挂服务键，Provider 注册到同一个键
==============================================================
  约定 ShellExecutor.service_key = shell
  约定是带服务键的类，模型 schema 另算一份，两者不绑在一起
[模型 schema] {'name': 'bash', 'description': '执行一条命令', 'parameters': {'cmd': 'string'}}
  装配本地实现
      [provide] shell <- LocalBashExecutor
  按服务键取回 LocalBashExecutor
```

约定是带服务键的 `ShellExecutor`，键名是 `shell`。Provider 通过 `install` 挂到这个键，Consumer 再按键取回。模型 schema 由 `prompt_schema` 单独给出，和执行器实现没有绑定关系。这回应了讲义第一节的三种变化。

### 场景 2：重复注册被拒绝

```
==============================================================
场景 2：一个 context 只装一个实现，重复注册被拒绝
==============================================================
      [provide] shell <- LocalBashExecutor
  已装本地执行器，再装沙箱执行器
  [reject] 服务键 'shell' 已挂 LocalBashExecutor，再挂 SandboxBashExecutor 被拒绝
  → 加载期失败，选择权在部署方，不在工具代码里
```

一个 context 只接受一个实现。装第二个时 `ctx.provide` 抛 `DuplicateServiceError`，对应上游加载期的重复服务失败。选择哪个实现是部署方的事，工具代码不参与。

### 场景 3：换实现不改 Consumer

```
==============================================================
场景 3：Consumer 只认服务键，换实现时它一行不改
==============================================================
  同一份 BashTool 类，先接本地实现
      [provide] shell <- LocalBashExecutor
      [inject] BashTool 取到服务键 shell -> LocalBashExecutor
   [run] local bash -c 'echo hi'
  再换沙箱实现，BashTool 定义不动
      [provide] shell <- SandboxBashExecutor
      [inject] BashTool 取到服务键 shell -> SandboxBashExecutor
   [run] sandbox confined 'echo hi'
  → 两次用的都是 BashTool，schema 只有一份，改动只发生在装配处
[模型 schema 仍是] {'name': 'bash', 'description': '执行一条命令', 'parameters': {'cmd': 'string'}}
```

同一个 `BashTool` 类接了两次，一次本地一次沙箱，类定义没动。`inject` 只列键名 `shell`，执行时调 `self.shell.execute(spec)`，全程不 import 两个具体实现。模型 schema 前后一致。这就是小测第 5 题没答出来的具体切法。

### 场景 4：约定断言与直接依赖的反例

```
==============================================================
场景 4：断言实现是约定类型，看直接依赖怎么破坏替换
==============================================================
  断言本地实现是约定类型 True
  断言沙箱实现是约定类型 True
  反例：Consumer 若直接 import 具体实现，换实现就得改它自己
   [run] local bash -c 'echo hi'
  → 要换成沙箱，必须把 LocalBashExecutor 改成 SandboxBashExecutor 并改这行调用
  → 每个持有具体实现的 Consumer 都要跟着动，这正是 seam 要避免的
```

两个实现都通过 `isinstance(impl, ShellExecutor)` 断言。反例里的 `TightlyCoupledTool` 直接持有 `LocalBashExecutor`，换沙箱就要改它自己的代码。持有具体实现的 Consumer 一旦多起来，替换的改动会顺着调用链扩散。

## 验收记录

| 项 | 结果 |
|---|---|
| 五道小测完成作答与判定 | 通过 |
| 讲义只留题目，批改进实践篇 | 通过 |
| mini-harness 第 6 讲代码与实测输出 | 通过 |

## 事实边界

题目和判定依据来自[第 6 讲讲义](lecture-6-capability-seam.md)，三条事实边界与源码落点沿用讲义所列 commit `4b399c39`。当时的回答为用户原话，判定为对照讲义后的结论。

骨架用类属性 `service_key` 和 `ctx.provide` 模拟上游的 `super(ctx, 'shell')`，省略了 Cordis 的 fiber 挂起与多键接线。本地和沙箱执行器返回固定字符串，不启动真实进程，目的是让换实现与按序对照稳定复现。四场景输出来自 `python3 demo.py` 的实际运行，逐字贴出。
