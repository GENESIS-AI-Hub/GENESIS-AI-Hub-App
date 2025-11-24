
import sys
import inspect
try:
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    with open('signature.txt', 'w') as f:
        f.write(str(inspect.signature(to_a2a)))
        f.write('\n')
        f.write(str(inspect.getdoc(to_a2a)))
except Exception as e:
    with open('signature.txt', 'w') as f:
        f.write(str(e))
