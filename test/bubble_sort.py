"""
冒泡排序算法实现及测试
"""

def bubble_sort(arr):
    """
    冒泡排序：重复遍历列表，比较相邻元素并交换顺序错误的元素。

    时间复杂度: O(n²)
    空间复杂度: O(1)
    稳定排序: 是
    """
    n = len(arr)
    # 复制一份，避免修改原列表（如果传入的是可变对象）
    result = arr[:]

    for i in range(n):
        # 优化：提前退出标志 —— 如果一轮没有发生交换，说明已经有序
        swapped = False
        # 每轮最后 i 个元素已经排好，无需再比较
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True
        if not swapped:
            break

    return result


def bubble_sort_inplace(arr):
    """冒泡排序（原地修改）"""
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr


def run_tests():
    """运行测试用例"""
    test_cases = [
        # (输入, 期望输出, 测试名称)
        ([64, 34, 25, 12, 22, 11, 90], [11, 12, 22, 25, 34, 64, 90], "普通乱序数组"),
        ([5, 1, 4, 2, 8],                [1, 2, 4, 5, 8],           "小数组"),
        ([1, 2, 3, 4, 5],                [1, 2, 3, 4, 5],           "已排序数组"),
        ([5, 4, 3, 2, 1],                [1, 2, 3, 4, 5],           "逆序数组"),
        ([1],                             [1],                        "单元素数组"),
        ([],                              [],                         "空数组"),
        ([3, 1, 2, 3, 1],                [1, 1, 2, 3, 3],           "有重复元素"),
        ([-3, -1, -7, 0, 10, 5],         [-7, -3, -1, 0, 5, 10],    "含负数和零"),
        ([2.5, 1.1, 3.9, 0.5],           [0.5, 1.1, 2.5, 3.9],      "浮点数数组"),
    ]

    results = []
    results.append("=" * 60)
    results.append("冒泡排序算法 -- 测试结果")
    results.append("=" * 60)
    results.append("")

    passed = 0
    failed = 0

    for input_arr, expected, name in test_cases:
        # 测试返回新列表的版本
        output = bubble_sort(input_arr)
        status = "[PASS]" if output == expected else "[FAIL]"

        results.append(f"测试: {name}")
        results.append(f"  输入:     {input_arr}")
        results.append(f"  期望输出: {expected}")
        results.append(f"  实际输出: {output}")
        results.append(f"  结果:     {status}")
        results.append("")

        if output == expected:
            passed += 1
        else:
            failed += 1

        # 验证原列表未被修改（非原地版本）
        original_copy = input_arr[:]
        _ = bubble_sort(input_arr)
        assert input_arr == original_copy, f"原列表被修改了: {input_arr} != {original_copy}"

    # 测试原地排序版本
    results.append("-" * 60)
    results.append("原地排序版本测试:")
    arr_inplace = [64, 34, 25, 12, 22, 11, 90]
    bubble_sort_inplace(arr_inplace)
    inplace_status = "[PASS]" if arr_inplace == [11, 12, 22, 25, 34, 64, 90] else "[FAIL]"
    results.append(f"  输入: [64, 34, 25, 12, 22, 11, 90]")
    results.append(f"  输出: {arr_inplace}")
    results.append(f"  结果: {inplace_status}")
    if arr_inplace == [11, 12, 22, 25, 34, 64, 90]:
        passed += 1
    else:
        failed += 1
    results.append("")

    # 性能测试
    results.append("-" * 60)
    results.append("性能测试（1000 个随机数）:")
    import time
    import random

    random.seed(42)
    large_arr = [random.randint(0, 10000) for _ in range(1000)]

    start = time.perf_counter()
    sorted_arr = bubble_sort(large_arr)
    elapsed = time.perf_counter() - start

    is_correct = sorted_arr == sorted(large_arr)
    results.append(f"  数据量: 1000")
    results.append(f"  耗时:   {elapsed:.6f} 秒")
    results.append(f"  正确性: {'[CORRECT]' if is_correct else '[ERROR]'}")
    results.append("")

    # 汇总
    results.append("=" * 60)
    results.append(f"汇总: 共 {passed + failed} 个测试, {passed} 通过, {failed} 失败")
    results.append("=" * 60)

    result_text = "\n".join(results)
    print(result_text)
    return result_text


if __name__ == "__main__":
    output_text = run_tests()

    # 将结果写入 txt 文件
    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write(output_text)

    print("\n>>测试结果已保存到 test_results.txt")
