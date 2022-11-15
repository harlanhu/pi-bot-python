from RPi import GPIO

# 设置引脚编码
GPIO.setmode(GPIO.BCM)
# 取消GPIO警告
GPIO.setwarnings(False)


def destroy():
    GPIO.cleanup()
