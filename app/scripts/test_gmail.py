
# import asyncio
# from aiosmtplib import SMTP

# async def test():
#     smtp = SMTP(hostname="smtp.gmail.com", port=587, start_tls=True, timeout=10)
#     await smtp.connect()
#     await smtp.login("createdliving1000@gmail.com", "mnbjkvphilhgrqlz")
#     print("SMTP works!")

# asyncio.run(test())


import smtplib, ssl

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "reatedliving1000@gmail.com"  # Enter your address
receiver_email = "edwardktwumasi1000@gmail.com"  # Enter receiver address
password = "mnbjkvphilhgrqlz"
message = """\
Subject: Hi there

This message is sent from Python."""


# Create a secure SSL context
context = ssl.create_default_context()

with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    res = server.login(sender_email, password)
    print(res)
    server.sendmail(sender_email, receiver_email, message)
    # TODO: Send email here