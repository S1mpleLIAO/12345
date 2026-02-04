/* ================= 工单列表（纯前端本地数据版 + 地址识别 + 智能派单整合） ================= */
(function () {
  // ====== 应用类型配置（不再需要暴露 API 密钥） ======
  const APP_TYPE_ADDRESS = "address_recognition";  // 地址识别
  const APP_TYPE_DISPATCH = "dispatch_assistant";  // 派单助手
  const USER_ID = "frontend-tickets-user";

  // ====== 你的工单数据（模拟） ======
  // 注意：真实场景下，这些字段初始可能为空，或者已有数据
  const TICKETS = [
    {
      "序号": 32902,
      "主要内容": "市民反映，自己是怀柔区汤河口镇东黄粱村的村民，市民拨打12345反映卜广生二层违建的事情，汤河口镇镇政府主管领导总以在“处理中\"为借口，欺上瞒下，不拆除，不作为，二层违建的地方怀柔区汤河口镇东黄粱村村中间，来电反映汤河口镇镇政府主管领导不作为的问题。注：请及时向反映人反馈办理信息",
      "被反映街乡镇": "怀柔区汤河口镇",
      "所在村社区": "东黄梁村",
      "二级承办单位简称": "汤河口镇",
      // --- 新增字段 ---
      "建议处置部门": "",
      "派单理由": "",
      "历史工单": [],
      "规则依据": [],
      "备注": ""
    },
    // ... 为了节省篇幅，这里复用您原有的数据，JS 运行时会自动处理 undefined ...
    {
      "序号": 32920,
      "主要内容": "市民反映，自己是怀柔区怀北镇椴树岭大队黄土梁村9号的村民，隔壁10号院是个老房，换成别处地，批了4间房的宅基地，却盖成了8间房，现在又回来盖了房子，改装成了民宿，灯火通明的，放泳池水，非常影响居民休息，认为对此建设村委会通过审批非常不合理，属于住宅区，地下建设民宿及多间房屋使用娱乐场所严重影响自家休息，希望尽快给出解决方案，自己是冠心病，希望地下设施拆除及停止相关扰民行为，地址：怀柔区怀北镇椴树岭大队黄土梁村幽谷神潭对面，市民表示这个房紧挨着自家的房子，肯定是超占，自己不认可给的答复，10号院的人批了两个宅基地，而且还办了两个本根本不符合要求，市民称问题一直未解决，如果合法的话，需要给自己出具法律条文，来电反映住宅区非法建设民宿希望拆除整改的问题。 注：通话中100秒处市民扬言称：如果他们老说合理合法不给我解决问题，我就上天安门，把房产证都拿出来咱们就亮亮象。注：市民现在地址怀柔区怀北镇椴树岭大队黄土梁村9号",
      "被反映街乡镇": "不详",
      "所在村社区": "椴树岭村",
      "二级承办单位简称": "怀北镇"
    },
    {
      "序号": 32932,
      "主要内容": "市民反映，自家在怀柔区桥梓镇凯甲庄村5号，邻居堵住了自家泄水沟，邻居棚子盖的也不合理，下雨会浇到自家房子上，自家邻居和自己有纠纷，大队书记迟迟不处理，且邻居养的兔子在自家卧室处，马上要下大雨了，自己怕房子无处排水给泡塌了，对此不认可，拖了两个月也没有人解决，打了一年多的12345，邻居是法院的，书记的同学，塑钢瓦的棚子下雨就漏进自己家，大队一直不帮解决，把自己取缔了，书记根本不理这茬，书记称打12345也没有用，欺上瞒下，势力大，打一年半载也解决不了，问题迟迟未得到解决，希望能有相关部门处理，希望反映到市里（已解释），书记根本就不称职，市民表示问题存在一年多了也没有相关部门联系自己解决问题，称问题没有得到解决，并且自己反映完未得到任何答复，对此不认可，事情没有得到解决，村委会根本就不解决问题，市民希望相关人员到现场进行查看，村书记无所作为，当初干涉了此问题，市民想了解是谁给的权力，村内有两位书记。市民称问题未解决，称桥梓镇已经被书记被买通了，向桥梓镇反映和没有反映一样，希望重新反映处理。市民说对方的狗一只骚扰自己睡不了觉，希望相关部门帮助解决邻居棚子违建问题，市民想知道自己反映很久一只没有得到解决，自己希望有关部门到现场查看（已解释），来电反映邻居棚子违建。 注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "不详",
      "所在村社区": "凯甲庄村",
      "二级承办单位简称": "桥梓镇"
    },
    {
      "序号": 32940,
      "主要内容": "市民反映，自家居住在怀柔区怀柔镇孟庄村，9月份村里进行美丽乡村改造，施工人员挖沟的时候，把自家的房子给震裂了，村委会到现场查看过，也承认此事，但是就一天推一天，一直不给解决，来电反映村内施工将房子震裂问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "不详",
      "所在村社区": "孟庄村",
      "二级承办单位简称": "怀柔镇"
    },
    {
      "序号": 32941,
      "主要内容": "市民反映，怀柔区雁栖镇乐园庄村125号，修路的修完了，但是自家门口有一个大水坑，是因为修路导致的，市民找修路的说了好几回，都没有解决这问题，来电反映门口大水坑无人解决注：请及时向反映人反馈办理情况。",
      "被反映街乡镇": "怀柔区雁栖镇",
      "所在村社区": "乐园庄村",
      "二级承办单位简称": "雁栖镇"
    },
    {
      "序号": 32947,
      "主要内容": "市民反映，自家住在怀柔区雁栖镇莲花池村，偷卖市民的树给开发商一个月了都没有给自己发放补偿款60万元左右，镇书记于勇贵（音似）吃拿卡要，自己不给他贿赂，他就不给自己补偿，对方联系自己表示解决问题需要吃拿卡要50%，不合理，来电反映镇书记吃拿卡要不给自己发放补偿款的问题。 注：请及时向反映人反馈办理情况。",
      "被反映街乡镇": "不详",
      "所在村社区": "莲花池村",
      "二级承办单位简称": "雁栖镇"
    },
    {
      "序号": 32952,
      "主要内容": "市民反映，编码3，自己10月3日上午去了河北省三河市燕郊，当天返回北京，自己距离疫情区有10公里多，10月5日健康宝出现弹窗，自己联系社区被告知要7天集中隔离，并没有告知自己原因，自己想居家隔离也可以，来京打工不容易集中隔离又是一笔不小的花费，自己觉得社区有点防疫过度了，姓名：邓俊彦，身份证号：41302619690912871X，健康宝手机号：13681473231，住址：怀柔区北房镇梨园庄村，梨园庄村村委会电话：13716038051，来电反映村防疫过度和集中隔离不合理问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区北房镇",
      "所在村社区": "梨园庄村",
      "二级承办单位简称": "北房镇"
    },
    {
      "序号": 32956,
      "主要内容": "市民反映，自己是怀柔区渤海镇四渡河村131号的居民，自己2015年到2019年举报渤海镇支书，黄学武，贺文海，乱砍承包果树，但是一直没有处理结果，后来他们联系相关部门把自己的低保给撤消了，给自己生活带来了很大的不便，反映之后没有回复，而且镇经管站不查书记的账目，市民的问题也得不到解决，市民此次来电反映，市民希望核桃树的钱给市民，8月-12月挑水钱也给市民，吃水井没有人给处理，需要开挖，称问题未得到解决，来电反映镇支书存在严重的以权谋私问题。 注：市民85秒称“拿着病例我找习近平去、我上中南海到东直门坐106，我拿着我的病例找习近平去”，120秒称“不然我就找习近平去”，注：市民居住在怀柔区渤海镇四渡河村131号注：请区分中心关注不稳定动态，2小时内回复市中心。",
      "被反映街乡镇": "怀柔区渤海镇",
      "所在村社区": "四渡河村",
      "二级承办单位简称": "渤海镇"
    },
    {
      "序号": 32961,
      "主要内容": "市民反映，举报怀柔区怀北镇椴树岭黄土梁村防疫岗六组李怀成组长，防疫过度，自己的客人扫码登记后不让进村以各种理由骚扰游客拒绝游客进村，让游客指定去哪家农家院才可以进，自家的可以通过，别人家的说不合规不让进，他的儿子和媳妇在防疫岗位态度恶劣，在躺椅坐着只有去指定的农家院才可以进，属于滥用职权公报私仇，来电希望解决防疫过度滥用职权问题，注：请及时来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区怀北镇",
      "所在村社区": "椴树岭村",
      "二级承办单位简称": "怀北镇"
    },
    {
      "序号": 32962,
      "主要内容": "市民反映，举报怀柔区怀北镇椴树岭黄土梁村防疫岗六组李怀成组长，家内占地违建门前有两个棚子属于私搭乱建，北山陶乐园房后私大乱建砍伐树木，私自搭建游乐场所，有集装箱，游泳池，和房塔，和儿童娱乐设施，私自占地，那是林地有树木李怀成私自砍伐，之前有人举报他被他找人给包庇了，来电希望解决私搭乱建问题，注：市民740秒称“不管我就上访北京，我跪地跪到北京，不是你死就是我亡，我现在就死让你们看着”，964秒称“挂了电话我就死给你们看我让你们12345也看看”，970秒称“如果你们处理不了你们解决不了那我今天就死在镇政府门口，我死在纪检委门口，我死到国家相关部门门口”，注：市民地址：怀柔区怀北镇椴树岭黄土梁村10号注：请区分中心关注不稳定动态，2小时内回复市中心。",
      "被反映街乡镇": "怀柔区怀北镇",
      "所在村社区": "椴树岭村",
      "二级承办单位简称": "怀北镇"
    },
    {
      "序号": 32964,
      "主要内容": "市民反映，自己住在怀柔区汤河口镇东黄梁村，村书记卜广生家1层是2019年盖的，经过了批示，现在在建设二层违建，没有经过批示，镇政府城建办和农业农村局9月5日已经定性违建，但一直没拆，9月20日卜广生家开始施工三层了，汤河口镇政府以怀柔区农业农村局不发函不发文为理由，对于村书记卜广生家的二层违建不拆除，对此不认可，来电反映汤河口镇政府不作为。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区汤河口镇",
      "所在村社区": "东黄梁村",
      "二级承办单位简称": "汤河口镇"
    },
    {
      "序号": 32965,
      "主要内容": "市民反映，编码3。自己在怀柔区庙城镇华欣湾小区b2108，姓名：衣鑫铜，身份证号码：220382199911132227，手机号：15222255454，来电反映新冠-健康宝弹窗问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区庙城镇",
      "所在村社区": "庙城社区",
      "二级承办单位简称": "庙城镇"
    },
    {
      "序号": 32969,
      "主要内容": "市民反映，市民住在怀柔区长哨营满族乡东石门村３号，村里别的住户都安排煤球，但是没有人给自己家安排，不清楚是什么原因，来电反映没有给安排煤球问题。‘注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区杨宋镇",
      "所在村社区": "耿辛庄村",
      "二级承办单位简称": "杨宋镇"
    },
    {
      "序号": 32970,
      "主要内容": "市民反映，市民住在怀柔区长哨营满族乡东石门村３号，现在停水了，属于自备井供水，来电反映停水问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区杨宋镇",
      "所在村社区": "耿辛庄村",
      "二级承办单位简称": "杨宋镇"
    },
    {
      "序号": 32977,
      "主要内容": "市民反映，在怀柔区汤河口镇东黄梁村书记东黄梁村是在建二层，这是属于违建的之前的时候反映了他们也停工了，但是今天又开始施工了，表示问题未得到解决，表示现在不止建二层，他们还在继续建三层，这不是欺负老百姓吗？这个违建在街中心，两边都有人住，把村民都挡住了，事情没有得到解决，房屋已经被判定违建让汤河口镇拆除，镇政府以怀柔区农业农村局没有发函为由没有拆除违建，市民要求镇政府拆除违建（已解释），来电反映镇政府不作为的问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区汤河口镇",
      "所在村社区": "东黄梁村",
      "二级承办单位简称": "汤河口镇"
    },
    {
      "序号": 32981,
      "主要内容": "市民反映，从珠海返京，社区联系自己，要求居家隔离，安装门磁，但珠海市7天前有一例，7天内无新增是不是不能居家隔离，是不是实时更新的，姓名蓝宇晴，身份证号是110227199102211528，居住地址在怀柔区龙山街道南华园三区，来电反映核实隔离政策注：请及时向反映人反馈办理情况。",
      "被反映街乡镇": "怀柔区龙山街道",
      "所在村社区": "四区社区",
      "二级承办单位简称": "龙山街道"
    },
    {
      "序号": 32983,
      "主要内容": "市民反映，自己住在怀柔区北房镇裕华园小区7号楼的自行车车棚上边的顶部多出破损，希望维修，来电反映帮助维修自行车车棚。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区北房镇",
      "所在村社区": "裕华园社区",
      "二级承办单位简称": "北房镇"
    },
    {
      "序号": 32988,
      "主要内容": "市民反映，怀柔区怀北镇椴树岭村李怀成家私砍树木，该问题以前被人举报过，当时都没人处理不了了之，砍伐树木的空出地，现在被李怀成建成了游乐场属于违建，来电反映乱砍树木及违建问题。注：请及时向来电人反馈办理信息。",
      "被反映街乡镇": "怀柔区怀北镇",
      "所在村社区": "椴树岭村",
      "二级承办单位简称": "怀北镇"
    },
    {
      "序号": 32990,
      "主要内容": "市民反映，怀柔区怀北镇椴树岭村，于秀芳农家院在周边进行了扩建市民表示都是违建，希望核实，如属实拆除，来电反映违建问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区怀北镇",
      "所在村社区": "椴树岭村",
      "二级承办单位简称": "怀北镇"
    },
    {
      "序号": 32991,
      "主要内容": "市民反映，怀柔区怀北镇椴树岭村李怀成家房屋超出房本使用面积，多占了村里一条街属于违建，来电反映房屋违建问题。注：请及时向来电人反馈办理信息。",
      "被反映街乡镇": "怀柔区怀北镇",
      "所在村社区": "椴树岭村",
      "二级承办单位简称": "怀北镇"
    },
    {
      "序号": 32992,
      "主要内容": "市民反映，自己是怀柔区泉河街道富乐小区北里40号院41号楼2单元102居民，楼上住户202野蛮装修，破坏房屋楼板，装修用电锤，剔凿时将楼板震松动，导致今年9.19号中午自家从楼板缝处漏水，将被褥、床垫和床泡湿，楼上房主熟视无睹，给他打过至少三次电话，都推三阻四不见面，让其女儿敷衍了事，完全不顾及邻居情面，现要求楼上房主给予恢复装修并当面道歉，对泡过的被褥、床垫和床给予五千元赔偿（已解释），要求转区住健委，彻查楼上违法违规行为，怀疑该装修队伍无资质施工，违规私改地暖，望区住建委从行业主管角度为百姓做主，希望联系怀柔区住建委和城管委（已解释），来电反映楼上住户装修破坏房屋楼板导致漏水问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "不详",
      "所在村社区": "富乐北里社区",
      "二级承办单位简称": "泉河街道"
    },
    {
      "序号": 32997,
      "主要内容": "市民反映，在怀柔区北房镇郑家庄村，村内开始收棒子需要进行晾晒，但是有人拍照不让晾，不晾又没有办法收，来电反映无法晾晒粮食的问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区北房镇",
      "所在村社区": "郑家庄村",
      "二级承办单位简称": "北房镇"
    },
    {
      "序号": 33000,
      "主要内容": "市民反映，自家住在怀柔区龙山街道南城社区后恒街7号院，老年活动中心没有灯，晚上不方便，无法活动，来电希望相关部门帮助解决老年活动站没有灯的问题。注：请及时向来电人反馈办理信息。",
      "被反映街乡镇": "怀柔区龙山街道",
      "所在村社区": "南城社区",
      "二级承办单位简称": "龙山街道"
    },
    {
      "序号": 33001,
      "主要内容": "市民反映，家住怀柔区桥梓镇圣泉公寓，7月份物业以罐装燃气有安全隐患为由就把燃气停了，换了特别小的燃气罐，要自行去燃气公司换气，现在天气越来越冷了，小燃气罐没法供暖，希望开通燃气管道，来电反映希望开通燃气管道。注：可联系方式13910814262注：请及时向反映人反馈处理进展。",
      "被反映街乡镇": "怀柔区桥梓镇",
      "所在村社区": "北宅村",
      "二级承办单位简称": "桥梓镇"
    },
    {
      "序号": 33005,
      "主要内容": "健康宝弹窗3，在京，市民反映，自己住在怀柔区庙城镇霍各庄村162号，从山西省洪洞县来京，还没有联系过村委会，姓名：孔祥利，身份证号：370881198402251550，健康宝绑定手机号：17316282369，来电反映健康宝弹窗问题。注：请及时向来电人反馈办理情况。",
      "被反映街乡镇": "怀柔区庙城镇",
      "所在村社区": "霍各庄村",
      "二级承办单位简称": "庙城镇"
    }
  ];

  // ... (DIFY_ADDR, DIFY_DISPATCH 配置 和 TICKETS 数据在此处，按您要求省略) ...

  // ====== 2) 状态 ======
  let state = {
    q: "",
    page: 1,
    size: 10,
    filtered: [...TICKETS], // Note: In real app, this refers to the TICKETS variable defined above
    currentItem: null,
    tempCorrectionRes: null, // Temporary storage for correction results
    tempDispatchRes: null    // Temporary storage for dispatch results
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
      contains(x["所在村社区"], q) ||
      contains(x["二级承办单位简称"], q) ||
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
  // ====== 修改点: renderTable 增加按钮禁用逻辑 ======
  function renderTable(){
    const tbody = $("ticketsTbody");
    const items = getPageItems();

    if (!items.length){
      tbody.innerHTML = `<tr><td colspan="11" class="tickets-empty">暂无数据</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(x => {
      // ✅ 核心判断：只有当“建议处置部门”和“派单理由”都有值时，才认为已分析，允许更正
      const hasAnalyzed = x["建议处置部门"] && x["派单理由"];

      return `
      <tr>
        <td class="td-center td-mono">${esc(x["序号"])}</td>
        <td title="${esc(x["主要内容"])}"><div class="td-clamp-2">${esc(x["主要内容"])}</div></td>
        <td class="td-center">${esc(x["被反映街乡镇"] || "—")}</td>
        <td class="td-center">${esc(x["所在村社区"] || "—")}</td>
        <td class="td-center">${esc(x["二级承办单位简称"] || "—")}</td>

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
          // 这里的 disabled 属性虽然在 HTML 上生效，但为了安全加个逻辑判断
          if (!item["建议处置部门"] || !item["派单理由"]) {
             return alert("请先在详情中进行智能派单分析！");
          }
          openCorrectionModal(item);
        }
      });
    });
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
          <div class="addr-modal-title">🤖 地址识别</div>
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
                <label class="ai-check"><input type="checkbox" id="chkCommunity" /> 覆盖所在村社区</label>
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
       if($("chkCommunity").checked) item["所在村社区"] = $("ai_community").textContent;
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
          <div class="addr-modal-title">🤖 智能派单助手</div>
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
               <div class="addr-panel-head"><div class="addr-panel-subtitle">🧾 历史工单参考</div></div>
               <div class="addr-panel-body" id="dp_history_box" style="max-height:200px; overflow:auto; font-size:12px;">
                 <div style="color:#94a3b8; padding:10px;">暂无数据</div>
               </div>
            </div>
            <div class="addr-panel">
               <div class="addr-panel-head"><div class="addr-panel-subtitle">📚 规则依据</div></div>
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
          <div class="addr-modal-title">🛠️ 智能更正</div>
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
                 <input id="cr_dept" class="correct-input" placeholder="例如：怀柔镇政府" />
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
            <div class="kv-item"><div class="kv-k">所在村社区</div><div class="kv-v" id="kv_community"></div><div class="kv-sub" id="kv_community_sub"></div></div>
            <div class="kv-item"><div class="kv-k">二级承办单位</div><div class="kv-v" id="kv_unit"></div></div>
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
                 <div class="addr-panel-subtitle" style="font-size:13px;">🧾 历史工单参考</div>
               </div>
               <div class="addr-panel-body" id="kv_history_list" style="max-height:180px; overflow:auto; padding:10px;"></div>
            </div>
            <div class="addr-panel">
               <div class="addr-panel-head" style="background:#f8fbff; border-bottom:1px solid #e2e8f0; padding:8px 12px;">
                 <div class="addr-panel-subtitle" style="font-size:13px;">📚 规则依据</div>
               </div>
               <div class="addr-panel-body" id="kv_rules_list" style="max-height:180px; overflow:auto; padding:10px;"></div>
            </div>
          </div>
          <div class="ticket-content">
            <div class="ticket-content-title">主要内容</div>
            <div class="ticket-content-text" id="kv_content"></div>
          </div>
          <div class="ticket-actions-bar">
            <div style="margin-right:auto; font-size:12px; color:#64748b;">💡 辅助工具：</div>
            <button id="btnOpenAddr" class="btn-primary" style="margin-right:10px; background:linear-gradient(180deg, #64748b, #475569);">🤖 地址识别</button>
            <button id="btnOpenDispatch" class="btn-primary">🚀 智能派单分析</button>
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
    $("kv_community").textContent = item["所在村社区"] || "不详";
    $("kv_unit").textContent = item["二级承办单位简称"] || "—";
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

  window.addEventListener("DOMContentLoaded", () => {
    if (!$("page-tickets")) return;
    applyFilter();
    renderAll();
  });

})();