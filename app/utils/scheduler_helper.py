def parse_cron(expression):
    """
    将 cron 字符串 (分 时 日 月 周) 解析为 APScheduler 参数
    """
    if not expression:
        return {}
        
    parts = expression.strip().split()
    if len(parts) != 5:
        # 如果格式不正确，尝试尽可能解析
        return {}
    
    return {
        'minute': parts[0],
        'hour': parts[1],
        'day': parts[2],
        'month': parts[3],
        'day_of_week': parts[4]
    }
