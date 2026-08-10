/* ================= 工单列表（纯前端本地数据版 + 地址识别 + 智能派单整合） ================= */
(function () {
  // ====== 应用类型配置（不再需要暴露 API 密钥） ======
  const APP_TYPE_ADDRESS = "address_recognition";  // 地址识别
  const APP_TYPE_DISPATCH = "dispatch_assistant";  // 派单助手
  const USER_ID = "frontend-tickets-user";

  // ====== 工单数据（可通过 Excel 上传替换） ======
  let TICKETS = [
  {
    "序号": 1,
    "主要内容": "服务对象年月初参加了开发区韩秀美容（地址：新景路世茂九龙庭，电话：）组织的云南旅游，后在云南旅游过程中再次报名了该店组织的月底到泰国旅游，并支付多元（无合同，有转账记录），但未去成，与商家协商退费未果，要求部门协调退费。（部门可联系）",
    "被反映街乡镇": "开发区",
    "投诉地点": "世茂九龙庭",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 2,
    "主要内容": "服务对象反映开发区新开苑居委会南侧、星海花园北门处的振兴东路段，有流动摊贩正在占道经营，希望部门尽快驱赶。",
    "被反映街乡镇": "开发区",
    "投诉地点": "星海花园",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 3,
    "主要内容": "服务对象是海尚家园西区-的业主，反映的业主在公共消防通道上违建，向物业反馈，物业却不处理，要求投诉物业不作为。",
    "被反映街乡镇": "开发区",
    "投诉地点": "海尚家园西区",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 4,
    "主要内容": "服务对象是开发区卓越府幢的业主，反映月日开发商强制交房，但号楼地下车库漏水，楼梯口没有灯黑乎乎的，且墙皮脱落渗水，地面湿滑，雾蒙蒙的，前期也多次发生过摔倒的事故，明明不具备交付条件那么房屋是如何通过验收的？要求投诉开发商强制交房。",
    "被反映街乡镇": "开发区",
    "投诉地点": "卓越府",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 5,
    "主要内容": "服务对象来电，反映崇州府的监控室的所有工作人员没有消控证，门口的保安也没有保安证，要求部门核查。",
    "被反映街乡镇": "开发区",
    "投诉地点": "崇州府",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 6,
    "主要内容": "服务对象吉地此呷（身份证：），在江苏南通市韩通赢吉重工有限公司（开发区东方大道号，老板李建：）做预处理工作，有劳动合同，现被拖欠月份工资左右，要求部门协调公司发放月份工资元。",
    "被反映街乡镇": "开发区",
    "投诉地点": "韩通赢吉重工有限公司",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 7,
    "主要内容": "服务对象前期“【欠薪】服务对象胡鹏程（身份证号：）曾反映年在开发区星辰花园、民主新村工地开挖机，工程已结束，承包单位：南通四建（通州区世纪大道号），负责人胡志玉，无负责人联系方式，拖欠年-月的工资万元，有合同。部门答复：已进一步督促南通四建集团公司待审计报告出来后，通知诉求人到南通四建办理对账手续，服务对象来电告知，四建集团一直未发放工资要求部门尽快处理发放工资。”部门答复：南通四建再次与诉求人联系，据调查了解，目前四条河项目的农民工工资均已结清，有结清承诺书及银行转账记录。本次诉求为机械租赁费，租赁合同为当事人与胡志玉（劳务分包负责人）签订，当事人与胡志玉之间的经济纠纷，建议走法律程序处理。服务对象表示不认可，认为自己是为南通四建进行工作，生活工资费用均是由南通四建进行发放，不存在什么租赁费，要求部门继续处理。",
    "被反映街乡镇": "开发区",
    "投诉地点": "星辰花园、民主新村",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 8,
    "主要内容": "服务对象反映在南通市华通钢绳有限公司东北角桥附近有人倾倒渣土（如图），要求部门管理并清除。",
    "被反映街乡镇": "开发区",
    "投诉地点": "华通钢绳有限公司",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 9,
    "主要内容": "服务对象来电反映茶百道（利群超市，开发区上海东路号）和开发区环境卫生管理有限公司（开发区环卫处，开发区民兴路号，），申请餐厨垃圾回收，近期发现部门不进行清运，电话联系被告知，需要把原材料、原材料包装分开，才能进行清运，原材料包装属于生活垃圾，要求部门电话联系自己给予合理的解释。（电话：）",
    "被反映街乡镇": "开发区",
    "投诉地点": "利群超市",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 10,
    "主要内容": "月日左右服务对象到开发区新河东路春天花园东门门口的华莱士花费元购买个鸡蛋饼并在鸡蛋饼内加辣加鸡腿，服务对象亲眼看到商家只加辣没有在鸡蛋饼内加鸡腿，投诉商家欺骗消费者，要求退还元。",
    "被反映街乡镇": "开发区",
    "投诉地点": "春天花园",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 11,
    "主要内容": "服务对象反映月日凌晨点左右在开发区星湖广场九公馆KTV唱歌，现场无价格公示，且要求强制消费项目，希望部门核查处理。",
    "被反映街乡镇": "开发区",
    "投诉地点": "星湖广场",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 12,
    "主要内容": "服务对象来电，反映瑞慈医院骨科住院部走廊里没有垃圾桶，要求部门协调增设垃圾桶。",
    "被反映街乡镇": "开发区",
    "投诉地点": "瑞慈医院",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 13,
    "主要内容": "服务对象是开发区富新园幢室的业主，月日晚上点多，在开发区新东路号南通世茂广场大润发(星湖店)购买了一只鸡，花费元。到家后服务对象发现鸡是臭的，后服务对象带着鸡前往大润发申请换货，工作人员刚开始同意次日换货，接到领导电话后工作人员认为服务对象无理取闹。（无商家电话，服务对象电话）",
    "被反映街乡镇": "开发区",
    "投诉地点": "南通世茂广场",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 14,
    "主要内容": "服务对象是开发区春风南岸号楼室业主，购房两年不到，人也没有住进去，月日却发现家中卫生间的瓷砖掉落，向物业保修，物业却说已过质保期，服务对象不认可，要求部门协调维修瓷砖。",
    "被反映街乡镇": "开发区",
    "投诉地点": "春风南岸",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 15,
    "主要内容": "商家名称:未知,商家电话:不清楚,消费类型:商品,商品品牌:澄鑫巴巴,消费金额:,是否网购:否,存在问题:安全与质量投诉,详细内容:月日南通智鼎电子科技有限公司门口小卖部（没有名字）买了两个沉鑫热狗香肠面包一瓶水一个热狗肠，吃到第二个热狗面包的时候，里边儿的热狗又硬又干，味道还发酸，看了一眼保质期才知道一个月过期，几天前就过期了还在卖，导致服务对象肚子疼，要求部门严肃处理，并检查商家所有手续证件，并要求按照消费者协议保护法进行赔偿。",
    "被反映街乡镇": "开发区",
    "投诉地点": "南通智鼎电子科技有限公司",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 16,
    "主要内容": "开发区中港白金大厦东门流动摊贩占道经营，要求部门驱赶。",
    "被反映街乡镇": "开发区",
    "投诉地点": "中港白金大厦",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 17,
    "主要内容": "服务对象来电反映开发区竹林路与新兴路交叉口有流动摊贩占道经营。要求部门驱赶。",
    "被反映街乡镇": "开发区",
    "投诉地点": "竹林路与新兴路交叉口",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 18,
    "主要内容": "服务对象来电，反映开发区住建局下属道路巡查维护项目有个标段，如皋水建公司承包的第二标段，应该是有个巡查人员名额，目前实际就任的只有人，剩下的个名额都是打的空卡，但是一样上报拿钱。要求部门核查处理。",
    "被反映街乡镇": "开发区",
    "投诉地点": "开发区住建局",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 19,
    "主要内容": "服务对象是开发区汇园小区幢号车库的业主，反映车库门口的下水道堵塞，物业称需要业主自己维修，服务对象不认可，要求部门协调疏通下水道。",
    "被反映街乡镇": "开发区",
    "投诉地点": "汇园小区",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 20,
    "主要内容": "服务对象前期来电，反映月日小海街道偷挖走了服务对象的祖坟（定海村组）一事，曾有部门答复。服务对象现再次来电称爷爷奶奶的骨灰盒至今没有找到，要求部门归还。",
    "被反映街乡镇": "小海街道",
    "投诉地点": "定海村",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 21,
    "主要内容": "服务对象是开发区新开街道绿地新里城幢室的业主，房屋购买时属于精装房，目前还属于五年质保期，因为卫生间防水没有做好，导致墙皮脱落，地板发黑，希望部门协调尽快处理卫生间防水问题。",
    "被反映街乡镇": "新开街道",
    "投诉地点": "绿地新里城",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 22,
    "主要内容": "服务对象来电，姓名：张镇 ，被南通沪通企业服务外包有限责任公司（崇川区新河路越秀城市广场楼）漏缴年、两月社保，故意拖欠，要求部门协调尽快补缴。",
    "被反映街乡镇": "崇川区",
    "投诉地点": "越秀城市广场",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 23,
    "主要内容": "服务对象来电，前期反映在开发区芭乐时尚美容美发(旺角商业广场店)（复兴东路旺角商业广场，无电话）办理了理发卡，剩余多元，现因工作调动，要离开南通，老板承诺天之内打钱给其，但要求到店取。服务对象表示自己无法呆这么久，在南通也无朋友家人，希望部门协调可以尽快把退款给其。部门已有答复，服务对象再次来电，称至今没有退款，负责人也不接电话了，且该店目前仍在经营，要求部门继续协调退款。",
    "被反映街乡镇": "开发区",
    "投诉地点": "旺角商业广场",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 24,
    "主要内容": "服务对象反映，月日上午点左右，开发区源兴花苑南门有大量流动摊贩，要求部门驱赶流动摊贩。",
    "被反映街乡镇": "开发区",
    "投诉地点": "源兴花苑",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 25,
    "主要内容": "服务对象是时光漫城业主，反映号楼东边空地建筑垃圾堆放，到处乱飞，影响小区业主生活，希望部门前去处理。",
    "被反映街乡镇": "开发区",
    "投诉地点": "时光漫城",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 26,
    "主要内容": "月日，开发区万和家园西侧广贤路有流动摊贩占道经营，要求部门长效管理。",
    "被反映街乡镇": "开发区",
    "投诉地点": "万和家园",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 27,
    "主要内容": "服务对象是开发区振兴东路号振兴花园号楼室的的业主，反映振兴花园号楼顶楼的伸缩缝的铁皮全部生锈破损了，因为时间长了，风化了，一下雨雨水就从伸缩缝流到楼楼，流到业主家里，已经通知物业，但是还是彻底处理，也向网格员、书记反映都表示无能无力，服务对象不认可，要求尽快维修振兴花园号楼顶楼的伸缩缝。",
    "被反映街乡镇": "开发区",
    "投诉地点": "振兴花园",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 28,
    "主要内容": "服务对象来电反映开发区龙田花苑一期号楼西单元的电梯坏了已有半个月，至今没有维修，到物业办公室反映，没有人管，只说马上会修，要求部门尽快检修电梯。",
    "被反映街乡镇": "开发区",
    "投诉地点": "龙田花苑",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 29,
    "主要内容": "服务对象来电，开发区航运学院地铁号口外的永安行车都没有电了，希望做好共享车维护的工作。",
    "被反映街乡镇": "开发区",
    "投诉地点": "航运学院",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  },
  {
    "序号": 30,
    "主要内容": "服务对象来电，反映开发区新开菜市场号卖肉的摊位上秤缺斤少两，服务对象在摊位买肉，摊主秤了重两，但服务对象在公平秤上秤是两，与市场管理人员反映，但管理人员只是将服务对象带到摊位上，让摊主退给服务对象元，也没有对摊主进行处罚或核查秤的问题，投诉市场管理人员不作为，要求部门核查菜市场号摊位及其他摊位的秤是否存在缺斤少两。",
    "被反映街乡镇": "开发区",
    "投诉地点": "新开菜市场",
    "建议处置部门": "",
    "派单理由": "",
    "历史工单": [],
    "规则依据": [],
    "备注": ""
  }
];

  // ... (DIFY_ADDR, DIFY_DISPATCH 配置 和 TICKETS 数据在此处，按您要求省略) ...

  // ====== 2) 状态 ======
  let state = {
    q: "",
    page: 1,
    size: 10,
    filtered: [...TICKETS],
    currentItem: null,
    tempCorrectionRes: null,
    tempDispatchRes: null,
    selected: new Set(),        // 选中的工单序号集合
    batchCancelled: false       // 批量处理取消标志
  };

  function $(id){ return document.getElementById(id); }

  function esc(s){
    return (s ?? "").toString().replace(/[&<>"']/g, (m)=>({
      "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
    }[m]));
  }

  function contains(hay, needle){
    return (hay ?? "").toString().toLowerCase().includes((needle ?? "").toString().toLowerCase());
  }

  function fmtList(arr){
    if(!Array.isArray(arr) || arr.length===0) return "";
    return `[${arr.length}条]`;
  }

  function applyFilter(){
    const q = state.q.trim();
    if (!q){
      state.filtered = [...TICKETS];
      return;
    }
    state.filtered = TICKETS.filter(x => (
      contains(x["主要内容"], q) ||
      contains(x["被反映街乡镇"], q) ||
      contains(x["投诉地点"], q) ||
      contains(x["建议处置部门"], q) ||
      contains(String(x["序号"]), q)
    ));
  }

  function getPageItems(){
    const start = (state.page - 1) * state.size;
    const end = start + state.size;
    return state.filtered.slice(start, end);
  }

  // ====== 修改点 1: 表格渲染 (renderTable) ======
  // ====== 修改点: renderTable 增加复选框和按钮禁用逻辑 ======
  function renderTable(){
    const tbody = $("ticketsTbody");
    const items = getPageItems();

    if (!items.length){
      tbody.innerHTML = `<tr><td colspan="11" class="tickets-empty">暂无数据</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(x => {
      const id = String(x["序号"]);
      const isChecked = state.selected.has(id);
      // ✅ 核心判断：只有当"建议处置部门"和"派单理由"都有值时，才认为已分析，允许更正
      const hasAnalyzed = x["建议处置部门"] && x["派单理由"];

      return `
      <tr data-id="${esc(id)}">
        <td class="td-center">
          <input type="checkbox" class="ticket-checkbox" data-id="${esc(id)}" ${isChecked ? "checked" : ""} />
        </td>
        <td class="td-center td-mono">${esc(x["序号"])}</td>
        <td title="${esc(x["主要内容"])}"><div class="td-clamp-2">${esc(x["主要内容"])}</div></td>
        <td class="td-center">${esc(x["被反映街乡镇"] || "—")}</td>
        <td class="td-center">${esc(x["投诉地点"] || "—")}</td>

        <td class="td-center" style="color:#1d4ed8; font-weight:700;">${esc(x["建议处置部门"] || "—")}</td>
        <td title="${esc(x["派单理由"])}"><div class="td-clamp-2" style="font-size:12px; color:#64748b;">${esc(x["派单理由"] || "—")}</div></td>
        <td class="td-center" style="font-size:12px;">${fmtList(x["历史工单"])}</td>
        <td class="td-center" style="font-size:12px;">${fmtList(x["规则依据"])}</td>
        <td class="td-center" style="font-size:12px; color:#94a3b8;">${esc(x["备注"] || "—")}</td>

        <td class="td-center">
          <button class="btn-mini" data-action="view" data-id="${esc(x["序号"])}">查看</button>

          <button class="btn-mini warning"
                  data-action="correct"
                  data-id="${esc(x["序号"])}"
                  ${hasAnalyzed ? "" : "disabled"}
                  title="${hasAnalyzed ? '点击进行更正' : '请先点击[查看]并运行智能分析'}">
            更正
          </button>
        </td>
      </tr>
    `}).join("");

    // 绑定复选框事件
    tbody.querySelectorAll(".ticket-checkbox").forEach(cb => {
      cb.addEventListener("change", () => {
        const id = cb.getAttribute("data-id");
        if (cb.checked) {
          state.selected.add(id);
        } else {
          state.selected.delete(id);
        }
        updateSelectAllCheckbox();
        updateBatchButtons();
      });
    });

    tbody.querySelectorAll("button[data-action]").forEach(btn => {
      btn.addEventListener("click", () => {
        const action = btn.getAttribute("data-action");
        const id = btn.getAttribute("data-id");
        const item = TICKETS.find(t => String(t["序号"]) === String(id));
        if (!item) return alert("未找到该工单");

        if (action === "view"){
          openTicketModal(item);
        }
        if (action === "correct"){
          if (!item["建议处置部门"] || !item["派单理由"]) {
             return alert("请先在详情中进行智能派单分析！");
          }
          openCorrectionModal(item);
        }
      });
    });
  }

  // 更新全选复选框状态
  function updateSelectAllCheckbox() {
    const selectAll = $("selectAllCheckbox");
    if (!selectAll) return;
    const pageItems = getPageItems();
    const pageIds = pageItems.map(x => String(x["序号"]));
    const allChecked = pageIds.length > 0 && pageIds.every(id => state.selected.has(id));
    const someChecked = pageIds.some(id => state.selected.has(id));
    selectAll.checked = allChecked;
    selectAll.indeterminate = someChecked && !allChecked;
  }

  // 更新批量操作按钮状态
  function updateBatchButtons() {
    // 清理无效的选中项
    const validIds = new Set(TICKETS.map(t => String(t["序号"])));
    const invalidIds = [];
    state.selected.forEach(id => {
      if (!validIds.has(id)) invalidIds.push(id);
    });
    invalidIds.forEach(id => state.selected.delete(id));

    const count = state.selected.size;
    const btnBatchAddr = $("btnBatchAddress");
    const btnBatchDispatch = $("btnBatchDispatch");
    const selectedCount = $("selectedCount");

    if (btnBatchAddr) btnBatchAddr.disabled = count === 0;
    if (btnBatchDispatch) btnBatchDispatch.disabled = count === 0;
    if (selectedCount) selectedCount.textContent = count > 0 ? `已选 ${count} 条` : "";
  }

  function renderPagination(){
    const wrap = $("ticketsPagination");
    const total = state.filtered.length;
    const totalPages = Math.max(1, Math.ceil(total / state.size));

    const btn = (label, page, disabled=false, active=false) => {
      const cls = ["page-btn", disabled ? "disabled": "", active ? "active": ""].join(" ");
      return `<button class="${cls}" data-page="${page}" ${disabled?"disabled":""}>${label}</button>`;
    };
    const maxShow = 7;
    let start = Math.max(1, state.page - Math.floor(maxShow/2));
    let end = Math.min(totalPages, start + maxShow - 1);
    start = Math.max(1, end - maxShow + 1);

    let html = "";
    html += btn("«", 1, state.page === 1);
    html += btn("‹", Math.max(1, state.page - 1), state.page === 1);
    for (let p = start; p <= end; p++){
      html += btn(String(p), p, false, p === state.page);
    }
    html += btn("›", Math.min(totalPages, state.page + 1), state.page === totalPages);
    html += btn("»", totalPages, state.page === totalPages);

    wrap.innerHTML = html;
    wrap.querySelectorAll("button[data-page]").forEach(b => {
      b.addEventListener("click", () => {
        const p = parseInt(b.getAttribute("data-page"), 10);
        if (!p || p === state.page) return;
        state.page = p;
        renderAll();
      });
    });
  }

  function renderAll(){
    $("ticketsTotal").textContent = `共 ${state.filtered.length} 条`;
    renderTable();
    renderPagination();
    updateSelectAllCheckbox();
    updateBatchButtons();
  }

  // ====== 3) Dify 调用工具函数 ======
  function safeJsonParse(str) {
    if (typeof str !== "string") return null;
    const s = str.trim();
    if (!s) return null;
    if (!((s.startsWith("{") && s.endsWith("}")) || (s.startsWith("[") && s.endsWith("]")))) return null;
    try { return JSON.parse(s); } catch { return null; }
  }

  // ✅ 改动：使用代理客户端，支持 inputs 对象传参 (query, correction_feedback, previous_result 等)
  async function runDifyWorkflow(inputsOrQuery, appType) {
    let inputs = {};
    if (typeof inputsOrQuery === "string") {
      inputs = { query: inputsOrQuery };
    } else {
      inputs = inputsOrQuery;
    }

    // 使用代理客户端运行工作流
    const data = await DifyProxyClient.runWorkflow(appType, inputs, { user: USER_ID });
    let outputs = data?.data?.outputs ?? data?.outputs ?? {};

    // 解析 outputs.text 是否为 JSON string
    let text = outputs.text ?? outputs.result ?? outputs.answer ?? outputs.output ?? "";
    if (typeof text === "string") {
      const parsed = safeJsonParse(text.replace(/```json/g, "").replace(/```/g, ""));
      if (parsed) return { ...parsed, raw: data };
    }
    // 如果 outputs 本身就是对象结构
    if (outputs && (outputs.department || outputs.town || outputs["镇街"] || outputs.dept)) {
      return { ...outputs, raw: data };
    }
    throw new Error("AI 返回格式无法解析");
  }

  // ====== 4) 地址识别 (旧逻辑保持) ======
  // 注意：需要确保 ensureAddrModal 存在，否则查看详情里的地址识别会报错
  // 这里简化展示，逻辑与之前一致

  async function runAddressWorkflow(text){
     const res = await runDifyWorkflow(text, APP_TYPE_ADDRESS);
     return {
      town: (res["镇街"] ?? "").toString().trim(),
      community: (res["社区"] ?? "").toString().trim(),
      scope: (res["范围"] ?? "").toString().trim(),
      raw: res
    };
  }

  function ensureAddrModal() {
    if (document.getElementById("addrModal")) return;
    const div = document.createElement("div");
    div.id = "addrModal";
    div.className = "addr-modal-mask";
    div.innerHTML = `
      <div class="addr-modal">
        <div class="addr-modal-head">
          <div class="addr-modal-title">������ 地址识别</div>
          <button class="addr-modal-close" id="addrModalClose">✕</button>
        </div>
        <div class="addr-modal-body">
          <div class="addr-panel">
            <div class="addr-panel-head">
              <div class="addr-panel-subtitle">识别结果</div>
              <div class="addr-panel-actions"><button id="btnAddrDetect" class="btn-primary">地址识别</button></div>
            </div>
            <div class="addr-panel-body">
              <div class="ai-row"><div class="ai-k">识别镇街</div><div class="ai-v" id="ai_town">—</div></div>
              <div class="ai-row"><div class="ai-k">识别社区</div><div class="ai-v" id="ai_community">—</div></div>
              <div class="ai-row"><div class="ai-k">范围</div><div class="ai-v" id="ai_scope">—</div></div>
              <div class="ai-choose">
                <label class="ai-check"><input type="checkbox" id="chkTown" /> 覆盖被反映街乡镇</label>
                <label class="ai-check"><input type="checkbox" id="chkCommunity" /> 覆盖投诉地点</label>
                <button id="btnApplyAddr" class="btn-ghost" disabled>应用覆盖</button>
              </div>
              <div class="ai-hint" id="ai_hint">点击“地址识别”后，可勾选要覆盖的字段，再点“应用覆盖”。</div>
            </div>
          </div>
        </div>
        <div class="addr-modal-foot"><button class="btn-ghost" id="addrModalOk">关闭</button></div>
      </div>`;
    document.body.appendChild(div);
    const close = () => div.classList.remove("show");
    $("addrModalClose").addEventListener("click", close);
    $("addrModalOk").addEventListener("click", close);
    div.addEventListener("click", (e) => { if (e.target === div) close(); });

    $("btnAddrDetect").addEventListener("click", async () => {
       const item = state.currentItem;
       if(!item) return;
       const btn = $("btnAddrDetect");
       const hint = $("ai_hint");
       btn.disabled=true; btn.textContent="识别中...";
       try {
         const res = await runAddressWorkflow(item["主要内容"]||"");
         $("ai_town").textContent = res.town||"—";
         $("ai_community").textContent = res.community||"—";
         $("ai_scope").textContent = res.scope||"—";
         $("chkTown").checked = !!res.town;
         $("chkCommunity").checked = !!res.community;
         $("btnApplyAddr").disabled = false;
         hint.textContent = "识别完成，请确认覆盖。";
       } catch(e) { alert(e.message); }
       finally { btn.disabled=false; btn.textContent="地址识别"; }
    });

    $("btnApplyAddr").addEventListener("click", () => {
       const item = state.currentItem;
       if($("chkTown").checked) item["被反映街乡镇"] = $("ai_town").textContent;
       if($("chkCommunity").checked) item["投诉地点"] = $("ai_community").textContent;
       renderModalItem(item, { townChanged: $("chkTown").checked, communityChanged: $("chkCommunity").checked });
       renderAll();
       close();
    });
  }

  function openAddrModal() {
     ensureAddrModal();
     $("ai_town").textContent="—"; $("ai_community").textContent="—";
     $("btnApplyAddr").disabled=true;
     document.getElementById("addrModal").classList.add("show");
  }

  // ====== 5) 智能派单分析 (旧逻辑保持，用于详情里的第一次分析) ======
  function ensureDispatchModal(){
    if (document.getElementById("dispatchModal")) return;

    const div = document.createElement("div");
    div.id = "dispatchModal";
    div.className = "addr-modal-mask";
    div.innerHTML = `
      <div class="addr-modal" style="width: min(900px, 96vw);">
        <div class="addr-modal-head">
          <div class="addr-modal-title">������ 智能派单助手</div>
          <button class="addr-modal-close" id="dispatchModalClose">✕</button>
        </div>
        <div class="addr-modal-body">
          <div class="addr-panel">
            <div class="addr-panel-head" style="background: linear-gradient(180deg, #fff, #f0fdf4); border-color:#bbf7d0;">
              <div class="addr-panel-subtitle" style="color:#166534;">✅ 推荐处置方案</div>
              <div class="addr-panel-actions">
                <button id="btnDispatchRun" class="btn-primary">开始分析</button>
              </div>
            </div>
            <div class="addr-panel-body">
              <div class="ai-row"><div class="ai-k">建议部门</div><div class="ai-v" id="dp_dept" style="color:#15803d; font-size:16px;">—</div></div>
              <div class="ai-row"><div class="ai-k">派单理由</div><div class="ai-v" id="dp_reason" style="line-height:1.6;">—</div></div>
            </div>
          </div>
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-top:14px;">
            <div class="addr-panel">
               <div class="addr-panel-head"><div class="addr-panel-subtitle">������ 历史工单参考</div></div>
               <div class="addr-panel-body" id="dp_history_box" style="max-height:200px; overflow:auto; font-size:12px;">
                 <div style="color:#94a3b8; padding:10px;">暂无数据</div>
               </div>
            </div>
            <div class="addr-panel">
               <div class="addr-panel-head"><div class="addr-panel-subtitle">������ 规则依据</div></div>
               <div class="addr-panel-body" id="dp_rules_box" style="max-height:200px; overflow:auto; font-size:12px;">
                 <div style="color:#94a3b8; padding:10px;">暂无数据</div>
               </div>
            </div>
          </div>
          <div class="ai-choose" style="margin-top:14px; border-top:1px solid #e2e8f0; padding-top:12px;">
            <label class="ai-check"><input type="checkbox" id="chkDpDept" checked /> 覆盖处置部门</label>
            <label class="ai-check"><input type="checkbox" id="chkDpReason" checked /> 覆盖派单理由</label>
            <label class="ai-check"><input type="checkbox" id="chkDpExtra" checked /> 关联历史与规则</label>
            <button id="btnApplyDispatch" class="btn-ghost" disabled style="margin-left:auto; border-color:#166534; color:#166534; font-weight:800;">✅ 采纳并应用</button>
          </div>
          <div class="ai-hint" id="dp_hint" style="text-align:right;">点击“开始分析”获取 AI 建议。</div>
        </div>
      </div>
    `;
    document.body.appendChild(div);

    const close = () => div.classList.remove("show");
    $("dispatchModalClose").addEventListener("click", close);
    div.addEventListener("click", (e) => { if (e.target === div) close(); });

    $("btnDispatchRun").addEventListener("click", async () => {
      const item = state.currentItem;
      if (!item) return;
      const btn = $("btnDispatchRun");
      const hint = $("dp_hint");

      btn.disabled = true;
      btn.textContent = "分析中...";
      hint.textContent = "正在调用派单助手分析工单内容...";

      try {
        const res = await runDifyWorkflow(item["主要内容"] || "", APP_TYPE_DISPATCH);
        $("dp_dept").textContent = res.department || res.dept || "未识别";
        $("dp_reason").textContent = res.reason || "无理由";
        
        const renderBox = (id, list, emptyTxt) => {
          const box = $(id);
          box.innerHTML = "";
          if (Array.isArray(list) && list.length) {
             list.slice(0, 3).forEach(h => {
               const d = document.createElement("div");
               d.style.marginBottom = "8px";
               d.style.paddingBottom = "8px";
               d.style.borderBottom = "1px dashed #e2e8f0";
               const t = (typeof h === 'string' ? h : (h.content || JSON.stringify(h)));
               d.textContent = t.slice(0, 100) + "...";
               box.appendChild(d);
             });
          } else {
             box.innerHTML = `<div style="color:#94a3b8; padding:10px;">${emptyTxt}</div>`;
          }
        };

        renderBox("dp_history_box", res.history, "无相关历史");
        renderBox("dp_rules_box", res.rules, "无相关规则");

        state.tempDispatchRes = res;
        $("btnApplyDispatch").disabled = false;
        hint.textContent = "分析完成，请确认后点击“采纳并应用”。";

      } catch (e) {
        alert("分析失败：" + e.message);
        hint.textContent = "分析失败：" + e.message;
      } finally {
        btn.disabled = false;
        btn.textContent = "重新分析";
      }
    });

    $("btnApplyDispatch").addEventListener("click", () => {
      const item = state.currentItem;
      const res = state.tempDispatchRes;
      if (!item || !res) return;

      if ($("chkDpDept").checked) item["建议处置部门"] = res.department || res.dept || "";
      if ($("chkDpReason").checked) item["派单理由"] = res.reason || "";
      if ($("chkDpExtra").checked) {
        item["历史工单"] = res.history || [];
        item["规则依据"] = res.rules || [];
      }
      renderModalItem(item);
      renderAll();
      close();
      alert("✅ 已采纳 AI 派单建议！");
    });
  }

  function openDispatchModal(){
    ensureDispatchModal();
    $("dp_dept").textContent = "—";
    $("dp_reason").textContent = "—";
    $("dp_history_box").innerHTML = '<div style="color:#94a3b8; padding:10px;">暂无数据</div>';
    $("dp_rules_box").innerHTML = '<div style="color:#94a3b8; padding:10px;">暂无数据</div>';
    $("dp_hint").textContent = "点击“开始分析”获取 AI 建议。";
    $("btnApplyDispatch").disabled = true;
    state.tempDispatchRes = null;
    document.getElementById("dispatchModal").classList.add("show");
  }

  // ====== 6) ✅ 智能更正弹窗 (新增逻辑) ======
  function ensureCorrectionModal() {
    if (document.getElementById("correctionModal")) return;

    const div = document.createElement("div");
    div.id = "correctionModal";
    div.className = "addr-modal-mask";
    div.innerHTML = `
      <div class="addr-modal" style="width: min(600px, 96vw);">
        <div class="addr-modal-head">
          <div class="addr-modal-title">������️ 智能更正</div>
          <button class="addr-modal-close" id="correctionModalClose">✕</button>
        </div>

        <div class="addr-modal-body">
          
          <div class="addr-panel" style="margin-bottom:15px;">
             <div class="addr-panel-head">
               <div class="addr-panel-subtitle">当前处置建议 (Previous Result)</div>
             </div>
             <div class="addr-panel-body">
               <div style="margin-bottom:10px;">
                 <label style="font-size:12px; font-weight:700; color:#64748b;">处置部门</label>
                 <input id="cr_dept" class="correct-input" placeholder="例如：镇政府" />
               </div>
               <div>
                 <label style="font-size:12px; font-weight:700; color:#64748b;">派单理由</label>
                 <textarea id="cr_reason" class="correct-textarea" placeholder="派单的具体理由..."></textarea>
               </div>
             </div>
          </div>

          <div class="addr-panel" style="border-color:#f59e0b;">
             <div class="addr-panel-head" style="background:#fffbeb; border-color:#fcd34d;">
               <div class="addr-panel-subtitle" style="color:#b45309;">✍️ 更正反馈 (Correction Feedback)</div>
             </div>
             <div class="addr-panel-body">
               <textarea id="cr_feedback" class="correct-textarea" style="min-height:100px; border-color:#fcd34d;" placeholder="请输入您的更正理由或反馈，例如：该地址实际属于雁栖镇管辖，请重新分析..."></textarea>
               
               <div style="margin-top:10px; display:flex; justify-content:flex-end;">
                  <button id="btnCorrectionRun" class="btn-primary" style="background:linear-gradient(180deg, #f59e0b, #d97706);">⚡️ 执行更正分析</button>
               </div>
             </div>
          </div>
          
          <div class="ai-hint" id="cr_hint" style="margin-top:10px; text-align:right;">输入更正理由后，点击“执行更正分析”。</div>

        </div>

        <div class="addr-modal-foot" style="justify-content: space-between;">
          <div style="font-size:12px; color:#94a3b8; display:flex; align-items:center;">
             <span id="cr_status_icon">⚪</span>&nbsp;<span id="cr_status_text">等待操作</span>
          </div>
          <div style="display:flex; gap:10px;">
            <button class="btn-ghost" id="correctionModalCancel">取消</button>
            <button class="btn-primary" id="correctionModalApply" disabled>✅ 确认并保存</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(div);

    const close = () => div.classList.remove("show");
    $("correctionModalClose").addEventListener("click", close);
    $("correctionModalCancel").addEventListener("click", close);
    div.addEventListener("click", (e) => { if (e.target === div) close(); });

    // === 核心逻辑：执行更正分析 ===
    $("btnCorrectionRun").addEventListener("click", async () => {
      const item = state.currentItem;
      if (!item) return;

      const feedback = $("cr_feedback").value.trim();
      if (!feedback) {
        alert("请先填写“更正反馈”内容！");
        return;
      }

      // 获取当前界面上的部门和理由作为 previous_result
      const currentDept = $("cr_dept").value.trim();
      const currentReason = $("cr_reason").value.trim();
      const previousResultStr = `处置部门：${currentDept}；派单理由：${currentReason}`;

      const btn = $("btnCorrectionRun");
      const hint = $("cr_hint");
      const statusIcon = $("cr_status_icon");
      const statusText = $("cr_status_text");

      btn.disabled = true;
      btn.textContent = "分析中...";
      hint.textContent = "正在提交更正反馈并重新分析...";
      statusIcon.textContent = "⏳";
      statusText.textContent = "AI 处理中...";

      try {
        // ✅ 构造参数：query + correction_feedback + previous_result
        const inputs = {
          query: item["主要内容"] || "",
          correction_feedback: feedback,
          previous_result: previousResultStr
        };

        // 调用派单助手 (使用代理)
        const res = await runDifyWorkflow(inputs, APP_TYPE_DISPATCH);

        // ✅ 分析成功，回填到上方的输入框
        $("cr_dept").value = res.department || res.dept || "";
        $("cr_reason").value = res.reason || "";
        
        // 也可以保存历史和规则到临时变量，以便“确认并保存”时使用
        state.tempCorrectionRes = res;

        hint.textContent = "分析完成！上方结果已更新，请确认无误后点击右下角保存。";
        statusIcon.textContent = "✅";
        statusText.textContent = "已获取新结果";
        $("correctionModalApply").disabled = false;

      } catch (e) {
        console.error(e);
        hint.textContent = "更正分析失败：" + e.message;
        statusIcon.textContent = "❌";
        statusText.textContent = "失败";
        alert("更正失败：" + e.message);
      } finally {
        btn.disabled = false;
        btn.textContent = "⚡️ 执行更正分析";
      }
    });

    // === 确认保存 ===
    $("correctionModalApply").addEventListener("click", () => {
      const item = state.currentItem;
      if (!item) return;

      // 保存界面上最终显示的值（用户可能在AI生成后又手动改了）
      item["建议处置部门"] = $("cr_dept").value.trim();
      item["派单理由"] = $("cr_reason").value.trim();
      
      // 如果有 AI 返回的附属信息（历史/规则），也一并更新
      if (state.tempCorrectionRes) {
        if (state.tempCorrectionRes.history) item["历史工单"] = state.tempCorrectionRes.history;
        if (state.tempCorrectionRes.rules) item["规则依据"] = state.tempCorrectionRes.rules;
      }

      renderAll();
      close();
      alert("更正已保存！");
    });
  }

  function openCorrectionModal(item) {
    ensureCorrectionModal();
    state.currentItem = item;
    
    // 初始化：填充当前数据
    $("cr_dept").value = item["建议处置部门"] || "";
    $("cr_reason").value = item["派单理由"] || "";
    $("cr_feedback").value = ""; // 清空反馈框
    
    $("cr_hint").textContent = "输入更正理由后，点击“执行更正分析”。";
    $("cr_status_icon").textContent = "⚪";
    $("cr_status_text").textContent = "就绪";
    $("correctionModalApply").disabled = true; 
    state.tempCorrectionRes = null;

    document.getElementById("correctionModal").classList.add("show");
  }

  // ====== 7) 详情弹窗 (包含查看历史规则列表的修复) ======
  function ensureModal(){
    if (document.getElementById("ticketModal")) return;

    const div = document.createElement("div");
    div.id = "ticketModal";
    div.className = "ticket-modal-mask";
    div.innerHTML = `
      <div class="ticket-modal" style="width: min(1000px, 98vw);">
        <div class="ticket-modal-head">
          <div class="ticket-modal-title">工单详情</div>
          <button class="ticket-modal-close" id="ticketModalClose">✕</button>
        </div>
        <div class="ticket-modal-body">
          <div class="ticket-kv">
            <div class="kv-item"><div class="kv-k">序号</div><div class="kv-v" id="kv_id"></div></div>
            <div class="kv-item"><div class="kv-k">被反映街乡镇</div><div class="kv-v" id="kv_town"></div><div class="kv-sub" id="kv_town_sub"></div></div>
            <div class="kv-item"><div class="kv-k">投诉地点</div><div class="kv-v" id="kv_community"></div><div class="kv-sub" id="kv_community_sub"></div></div>
          </div>
          <div style="margin-top:12px; display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
             <div class="kv-item" style="border-color:#bbf7d0; background:#f0fdf4;">
                <div class="kv-k" style="color:#166534;">⚡️ 建议处置部门</div>
                <div class="kv-v" id="kv_dispatch_dept" style="color:#15803d;">—</div>
             </div>
             <div class="kv-item" style="border-color:#e2e8f0; background:#f8fafc;">
                <div class="kv-k">⚡️ 派单理由</div>
                <div class="kv-v" id="kv_dispatch_reason" style="font-size:14px; line-height:1.5;">—</div>
             </div>
          </div>
          <div class="ticket-detail-refs" style="margin-top:12px; display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
            <div class="addr-panel">
               <div class="addr-panel-head" style="background:#f8fbff; border-bottom:1px solid #e2e8f0; padding:8px 12px;">
                 <div class="addr-panel-subtitle" style="font-size:13px;">������ 历史工单参考</div>
               </div>
               <div class="addr-panel-body" id="kv_history_list" style="max-height:180px; overflow:auto; padding:10px;"></div>
            </div>
            <div class="addr-panel">
               <div class="addr-panel-head" style="background:#f8fbff; border-bottom:1px solid #e2e8f0; padding:8px 12px;">
                 <div class="addr-panel-subtitle" style="font-size:13px;">������ 规则依据</div>
               </div>
               <div class="addr-panel-body" id="kv_rules_list" style="max-height:180px; overflow:auto; padding:10px;"></div>
            </div>
          </div>
          <div class="ticket-content">
            <div class="ticket-content-title">主要内容</div>
            <div class="ticket-content-text" id="kv_content"></div>
          </div>
          <div class="ticket-actions-bar">
            <div style="margin-right:auto; font-size:12px; color:#64748b;">������ 辅助工具：</div>
            <button id="btnOpenAddr" class="btn-primary" style="margin-right:10px; background:linear-gradient(180deg, #64748b, #475569);">������ 地址识别</button>
            <button id="btnOpenDispatch" class="btn-primary">������ 智能派单分析</button>
          </div>
        </div>
        <div class="ticket-modal-foot"><button class="btn-ghost" id="ticketModalOk">关闭</button></div>
      </div>`;
    document.body.appendChild(div);
    const close = () => div.classList.remove("show");
    $("ticketModalClose").addEventListener("click", close);
    $("ticketModalOk").addEventListener("click", close);
    div.addEventListener("click", (e) => { if (e.target === div) close(); });

    $("btnOpenAddr").addEventListener("click", () => {
      if (!state.currentItem) return;
      openAddrModal();
    });
    $("btnOpenDispatch").addEventListener("click", () => {
      if (!state.currentItem) return;
      openDispatchModal();
    });
  }

  function renderModalItem(item, opts = {}){
    $("kv_id").textContent = item["序号"];
    $("kv_town").textContent = item["被反映街乡镇"] || "不详";
    $("kv_community").textContent = item["投诉地点"] || "不详";
    $("kv_content").textContent = item["主要内容"] || "";
    $("kv_town_sub").textContent = (opts.townChanged ? `已更新（识别：${opts.newTown || ""}）` : "");
    $("kv_community_sub").textContent = (opts.communityChanged ? `已更新（识别：${opts.newCommunity || ""}）` : "");

    $("kv_dispatch_dept").textContent = item["建议处置部门"] || "—";
    $("kv_dispatch_reason").textContent = item["派单理由"] || "—";

    const renderList = (containerId, list, emptyText) => {
      const box = $(containerId);
      box.innerHTML = "";
      if (!Array.isArray(list) || list.length === 0) {
        box.innerHTML = `<div style="color:#94a3b8; font-size:12px; font-style:italic;">${emptyText}</div>`;
        return;
      }
      list.forEach((item, idx) => {
        let text = "";
        if (typeof item === "string") text = item;
        else if (item && item.content) text = item.content;
        else text = JSON.stringify(item);

        const row = document.createElement("div");
        row.style.marginBottom = "8px";
        row.style.paddingBottom = "8px";
        row.style.borderBottom = "1px dashed #eff6ff";
        row.style.fontSize = "12px";
        row.style.lineHeight = "1.5";
        row.style.color = "#334155";
        row.innerHTML = `<span style="color:#2563eb; font-weight:bold; margin-right:4px;">${idx+1}.</span>${esc(text)}`;
        box.appendChild(row);
      });
    };
    renderList("kv_history_list", item["历史工单"], "暂无关联历史工单");
    renderList("kv_rules_list", item["规则依据"], "暂无关联规则");
  }

  function openTicketModal(item){
    ensureModal();
    state.currentItem = item;
    $("kv_town_sub").textContent = "";
    $("kv_community_sub").textContent = "";
    renderModalItem(item);
    document.getElementById("ticketModal").classList.add("show");
  }

  // ====== 8) Excel 上传功能 ======
  async function uploadExcel(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/api/tickets/upload", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "上传失败");
    }

    return await response.json();
  }

  function setupExcelUpload() {
    const uploadBtn = $("btnUploadExcel");
    const fileInput = $("excelFileInput");

    if (!uploadBtn || !fileInput) return;

    uploadBtn.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      uploadBtn.disabled = true;
      uploadBtn.textContent = "上传中...";

      try {
        const result = await uploadExcel(file);
        // 重要：先清空选中状态，再替换数据
        state.selected = new Set();  // 重新创建 Set，确保完全清空
        TICKETS = result.tickets;
        state.filtered = [...TICKETS];
        state.page = 1;
        applyFilter();
        renderAll();
        alert(`成功导入 ${result.count} 条工单`);
      } catch (err) {
        alert("上传失败：" + err.message);
      } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = "上传 Excel";
        fileInput.value = "";
      }
    });
  }

  // ====== 9) 批量处理进度弹窗 ======
  function ensureBatchModal() {
    if (document.getElementById("batchModal")) return;

    const div = document.createElement("div");
    div.id = "batchModal";
    div.className = "addr-modal-mask";
    div.innerHTML = `
      <div class="addr-modal" style="width: min(700px, 96vw);">
        <div class="addr-modal-head">
          <div class="addr-modal-title" id="batchModalTitle">批量处理</div>
          <button class="addr-modal-close" id="batchModalClose">✕</button>
        </div>
        <div class="addr-modal-body">
          <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
              <span id="batchProgressText">进度：0 / 0</span>
              <span id="batchProgressPercent">0%</span>
            </div>
            <div style="background: #e2e8f0; border-radius: 4px; height: 8px; overflow: hidden;">
              <div id="batchProgressBar" style="background: linear-gradient(90deg, #3b82f6, #1d4ed8); height: 100%; width: 0%; transition: width 0.3s;"></div>
            </div>
          </div>
          <div style="border: 1px solid #e2e8f0; border-radius: 8px; max-height: 400px; overflow-y: auto;" id="batchResultList">
            <div style="padding: 20px; color: #94a3b8; text-align: center;">等待开始...</div>
          </div>
        </div>
        <div class="addr-modal-foot" style="justify-content: space-between;">
          <div id="batchSummary" style="font-size: 12px; color: #64748b;"></div>
          <div>
            <button class="btn-ghost" id="batchModalCancel" style="margin-right: 10px;">取消</button>
            <button class="btn-primary" id="batchModalOk" disabled>完成</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(div);

    $("batchModalClose").addEventListener("click", () => {
      state.batchCancelled = true;
    });
    $("batchModalCancel").addEventListener("click", () => {
      state.batchCancelled = true;
    });
    $("batchModalOk").addEventListener("click", () => {
      div.classList.remove("show");
    });
  }

  function openBatchModal(title) {
    ensureBatchModal();
    $("batchModalTitle").textContent = title;
    $("batchProgressText").textContent = "进度：0 / 0";
    $("batchProgressPercent").textContent = "0%";
    $("batchProgressBar").style.width = "0%";
    $("batchResultList").innerHTML = '<div style="padding: 20px; color: #94a3b8; text-align: center;">准备中...</div>';
    $("batchSummary").textContent = "";
    $("batchModalCancel").disabled = false;
    $("batchModalOk").disabled = true;
    state.batchCancelled = false;
    document.getElementById("batchModal").classList.add("show");
  }

  function updateBatchProgress(completed, total, successCount, failCount) {
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    $("batchProgressText").textContent = `进度：${completed} / ${total}`;
    $("batchProgressPercent").textContent = `${percent}%`;
    $("batchProgressBar").style.width = `${percent}%`;
    $("batchSummary").textContent = `成功 ${successCount} 条，失败 ${failCount} 条`;
  }

  function addBatchResultItem(id, content, status, result) {
    const list = $("batchResultList");
    if (list.querySelector(".batch-placeholder")) {
      list.innerHTML = "";
    }

    const truncatedContent = content.length > 50 ? content.substring(0, 50) + "..." : content;
    const statusIcon = status === "success" ? "✓" : status === "error" ? "✗" : "⋯";
    const statusColor = status === "success" ? "#16a34a" : status === "error" ? "#dc2626" : "#f59e0b";

    const item = document.createElement("div");
    item.id = `batch-item-${id}`;
    item.style.cssText = "padding: 12px 15px; border-bottom: 1px solid #f1f5f9;";
    item.innerHTML = `
      <div style="display: flex; align-items: flex-start; gap: 10px;">
        <span style="color: ${statusColor}; font-weight: bold; font-size: 16px; flex-shrink: 0;">${statusIcon}</span>
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 13px; color: #334155; margin-bottom: 4px;">
            <span style="color: #64748b; font-weight: 600;">#${id}</span>
            ${esc(truncatedContent)}
          </div>
          <div style="font-size: 12px; color: ${statusColor};">
            → ${esc(result)}
          </div>
        </div>
      </div>
    `;
    list.appendChild(item);
    list.scrollTop = list.scrollHeight;
  }

  function updateBatchResultItem(id, status, result) {
    const item = document.getElementById(`batch-item-${id}`);
    if (!item) return;

    const statusIcon = status === "success" ? "✓" : status === "error" ? "✗" : "⋯";
    const statusColor = status === "success" ? "#16a34a" : status === "error" ? "#dc2626" : "#f59e0b";

    const iconSpan = item.querySelector("span");
    const resultDiv = item.querySelector("div > div:last-child");

    if (iconSpan) {
      iconSpan.textContent = statusIcon;
      iconSpan.style.color = statusColor;
    }
    if (resultDiv) {
      resultDiv.style.color = statusColor;
      resultDiv.innerHTML = `→ ${esc(result)}`;
    }
  }

  function finishBatchModal() {
    $("batchModalCancel").disabled = true;
    $("batchModalOk").disabled = false;
  }

  // ====== 10) 批量处理逻辑（并发控制） ======
  async function batchProcess(type) {
    // 清理无效的选中项（确保选中的序号在当前 TICKETS 中存在）
    const validIds = new Set(TICKETS.map(t => String(t["序号"])));
    const invalidIds = [];
    state.selected.forEach(id => {
      if (!validIds.has(id)) invalidIds.push(id);
    });
    invalidIds.forEach(id => state.selected.delete(id));

    const selectedIds = Array.from(state.selected);
    if (selectedIds.length === 0) {
      alert("请先选择要处理的工单");
      return;
    }

    const title = type === "address" ? "批量地址识别" : "批量派单分析";
    openBatchModal(title);

    const total = selectedIds.length;
    let completed = 0;
    let successCount = 0;
    let failCount = 0;

    const CONCURRENCY = 3;
    let running = 0;
    let index = 0;

    // 先添加所有待处理项
    for (const id of selectedIds) {
      const item = TICKETS.find(t => String(t["序号"]) === id);
      if (item) {
        addBatchResultItem(id, item["主要内容"] || "", "pending", "处理中...");
      }
    }

    const processOne = async (id) => {
      const item = TICKETS.find(t => String(t["序号"]) === id);
      if (!item) {
        failCount++;
        updateBatchResultItem(id, "error", "未找到工单");
        return;
      }

      try {
        if (type === "address") {
          const res = await runAddressWorkflow(item["主要内容"] || "");
          item["被反映街乡镇"] = res.town || item["被反映街乡镇"];
          item["投诉地点"] = res.community || item["投诉地点"];
          updateBatchResultItem(id, "success", `${res.town || "—"} / ${res.community || "—"}`);
          successCount++;
        } else {
          const res = await runDifyWorkflow(item["主要内容"] || "", APP_TYPE_DISPATCH);
          item["建议处置部门"] = res.department || res.dept || "";
          item["派单理由"] = res.reason || "";
          item["历史工单"] = res.history || [];
          item["规则依据"] = res.rules || [];
          const dept = res.department || res.dept || "未识别";
          const reason = (res.reason || "").substring(0, 30);
          updateBatchResultItem(id, "success", `建议部门：${dept} | ${reason}...`);
          successCount++;
        }
        // 实时更新表格行
        renderAll();
      } catch (e) {
        failCount++;
        updateBatchResultItem(id, "error", `失败：${e.message}`);
      }

      completed++;
      updateBatchProgress(completed, total, successCount, failCount);
    };

    // 并发控制执行
    const executeWithConcurrency = () => {
      return new Promise((resolve) => {
        const checkAndRun = () => {
          if (state.batchCancelled) {
            // 取消后标记剩余为取消
            while (index < selectedIds.length) {
              const id = selectedIds[index];
              updateBatchResultItem(id, "error", "已取消");
              failCount++;
              completed++;
              index++;
            }
            updateBatchProgress(completed, total, successCount, failCount);
            resolve();
            return;
          }

          while (running < CONCURRENCY && index < selectedIds.length) {
            const id = selectedIds[index];
            index++;
            running++;

            processOne(id).finally(() => {
              running--;
              checkAndRun();
            });
          }

          if (running === 0 && index >= selectedIds.length) {
            resolve();
          }
        };

        checkAndRun();
      });
    };

    await executeWithConcurrency();
    finishBatchModal();
    renderAll();
  }

  // ====== 11) 全选功能 ======
  function setupSelectAll() {
    const selectAll = $("selectAllCheckbox");
    if (!selectAll) return;

    selectAll.addEventListener("change", () => {
      const pageItems = getPageItems();
      const pageIds = pageItems.map(x => String(x["序号"]));

      if (selectAll.checked) {
        pageIds.forEach(id => state.selected.add(id));
      } else {
        pageIds.forEach(id => state.selected.delete(id));
      }

      renderTable();
      updateBatchButtons();
    });
  }

  // ====== 12) 批量操作按钮绑定 ======
  function setupBatchButtons() {
    const btnBatchAddr = $("btnBatchAddress");
    const btnBatchDispatch = $("btnBatchDispatch");

    if (btnBatchAddr) {
      btnBatchAddr.addEventListener("click", () => batchProcess("address"));
    }
    if (btnBatchDispatch) {
      btnBatchDispatch.addEventListener("click", () => batchProcess("dispatch"));
    }
  }

  window.addEventListener("DOMContentLoaded", () => {
    if (!$("page-tickets")) return;
    applyFilter();
    renderAll();
    setupExcelUpload();
    setupSelectAll();
    setupBatchButtons();
  });

})();