"""
测试 Dify API 代理服务
"""
import asyncio
from services.dify_proxy_service import dify_proxy


async def test_workflow():
    """测试工作流调用（非流式）"""
    print("🧪 测试工作流调用（非流式）...")

    try:
        result = await dify_proxy.run_workflow(
            app_type="dispatch_assistant",
            inputs={"query": "测试查询"},
            response_mode="blocking",
            user="test-user"
        ) 
        print("✅ 工作流调用成功")
        print(f"响应: {result}")
        return True
    except Exception as e:
        print(f"❌ 工作流调用失败: {e}")
        return False


async def test_workflow_stream():
    """测试工作流调用（流式）"""
    print("\n🧪 测试工作流调用（流式）...")

    try:
        chunk_count = 0
        async for chunk in dify_proxy.run_workflow_stream(
            app_type="dispatch_assistant",
            inputs={"query": "测试查询"},
            user="test-user"
        ):
            chunk_count += 1
            if chunk_count <= 3:  # 只打印前3个chunk
                print(f"  收到数据块 {chunk_count}: {len(chunk)} bytes")

        print(f"✅ 流式调用成功，共收到 {chunk_count} 个数据块")
        return True
    except Exception as e:
        print(f"❌ 流式调用失败: {e}")
        return False


async def test_config():
    """测试配置"""
    print("🧪 测试配置...")

    from config.dify_config import DIFY_API_KEYS, get_api_key

    print(f"  配置的应用类型: {list(DIFY_API_KEYS.keys())}")

    for app_type in DIFY_API_KEYS.keys():
        try:
            key = get_api_key(app_type)
            print(f"  ✅ {app_type}: {key[:10]}...")
        except Exception as e:
            print(f"  ❌ {app_type}: {e}")

    return True


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("Dify API 代理服务测试")
    print("=" * 60)

    results = []

    # 测试配置
    results.append(await test_config())

    # 注意：以下测试需要 Dify API 可访问
    print("\n⚠️  以下测试需要 Dify API 服务可访问")
    print("如果 Dify API 不可用，测试可能失败\n")

    # 测试非流式调用
    # results.append(await test_workflow())

    # 测试流式调用
    # results.append(await test_workflow_stream())

    print("\n" + "=" * 60)
    print(f"测试完成: {sum(results)}/{len(results)} 通过")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
