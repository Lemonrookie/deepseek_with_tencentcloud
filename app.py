# app.py (后端)
from flask import Flask, render_template, request, jsonify, session
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.lkeap.v20240522 import lkeap_client, models

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

tencentAPIid = "你申请的腾讯云API ID"
tencentAPIkey = "你申请的腾讯云API KEY"



# 初始化腾讯云客户端
def init_client():
    cred = credential.Credential(tencentAPIid, tencentAPIkey)
    http_profile = HttpProfile()
    http_profile.endpoint = "lkeap.tencentcloudapi.com"
    client_profile = ClientProfile()
    client_profile.timeout = 40000
    client_profile.httpProfile = http_profile
    return lkeap_client.LkeapClient(cred, "ap-guangzhou", client_profile)


@app.route('/')
def index():
    return render_template('chatds.html')


@app.route('/chat', methods=['POST'])
def chat():
    client = init_client()
    req = models.ChatCompletionsRequest()

    if 'messages' not in session:
        session['messages'] = []

    try:
        user_input = request.json['message'].strip()
        if not user_input:
            return jsonify({'error': '输入不能为空'}), 400

        # 构建消息记录
        session['messages'].append({
            "Role": "user",
            "Content": user_input,
            "ReasoningContent": "无"
        })

        # API请求
        params = {
            "Model": "deepseek-r1",
            "Messages": session['messages'],
            "Stream": False
        }
        req.from_json_string(json.dumps(params))
        resp = client.ChatCompletions(req)

        # 保存回复
        session['messages'].append({
            "Role": "assistant",
            "Content": resp.Choices[0].Message.Content,
            "ReasoningContent": resp.Choices[0].Message.ReasoningContent
        })

        return jsonify({
            'content': resp.Choices[0].Message.Content.strip(),
            'reasoning': resp.Choices[0].Message.ReasoningContent.strip()
        })

    except TencentCloudSDKException as err:
        return jsonify({'error': f"API错误: {err}"}), 500
    except Exception as e:
        return jsonify({'error': f"系统错误: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
