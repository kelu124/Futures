def getWeaksignals():
    functions = [
            {
            "name": "get_weaksignals",
            "description": "If the user asks for weak signals, act like a Futurist, process the text and extract if you can a list of weak signals. DO not invent anything, stick to what is explicitly detailed or can be inferred directly from the text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "signals": {
                        "type": 'array',
                        "items": {
                            "type": 'object',
                            "description": "A weak signal, as you have identified.",
                            "properties": {
                                "name" :{
                                    "type": 'string',
                                    "description": 'A name for this weak signal'
                                },
                                "description" :{
                                    "type": 'string',
                                    "description": 'A short description of this week signal, in 10 to 20 words.'
                                },
                                "change" :{
                                    "type": 'string',
                                    "description": 'This signals a change, precise a change from what to what. 15–20 word summary.'
                                },
                                "10-year" :{
                                    "type": 'string',
                                    "description": 'What might be different in 10 years time because of this weak signal? 15–20 word summary.'
                                },
                                "driving-force" :{
                                    "type": 'string',
                                    "description": 'What’s one driving force, or motivation, behind this change? 15–20 word summary.'
                                },
                                "relevancy" :{
                                    "type": 'integer',
                                    "description": 'Your appreciation of the relevancy and importance of the signal. 0 is really weak, 5 is strong and shouldnt be missed.'
                                }                                
                            },
                            "required": ["name","description","change","10-year","driving-force","relevancy"],
                        }
                    },
                },
                "required": ["signals"],
            },
        }
    ]
    return functions





def getEmergingIssues():
    functions = [
            {
            "name": "get_emergingissues",
            "description": "If the user asks for emerging issues, act like a Futurist, process the text and extract if you can a list of emerging issues (which are defined as issues may be tangentially of importance today, but may grow to wider concerns later on). Do not invent anything, stick to what is explicitly detailed or can be inferred directly from the text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issues": {
                        "type": 'array',
                        "items": {
                            "type": 'object',
                            "description": "An emerging issue, as you have identified.",
                            "properties": {
                                "name" :{
                                    "type": 'string', 
                                    "description": 'A name for this emerging issue'
                                },
                                "description" :{
                                    "type": 'string', 
                                    "description": 'A short description of this emerging issue, in 10 to 30 words.'
                                },
                                "relevancy" :{
                                    "type": 'integer', 
                                    "description": 'Your appreciation of the relevancy and importance of the issue. 0 is really weak, 5 is strong and shouldnt be missed.'
                                }                                
                            },
                            "required": ["name","description","relevancy"],
                        }
                    },
                },
                "required": ["issues"],
            },
        }
    ]
    return functions




def getEmergingTechnologies():
    functions = [
            {
            "name": "get_emergingtechnologies",
            "description": "If the user asks for emerging technologies, act like a Futurist, process the text and extract if you can a list of emerging technologies. Do not invent anything, stick to what is explicitly detailed or can be inferred directly from the text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "technology": {
                        "type": 'array',
                        "items": {
                            "type": 'object',
                            "description": "An emerging technology, as you have identified.",
                            "properties": {
                                "name" :{
                                    "type": 'string', 
                                    "description": 'A name for this emerging technology'
                                },
                                "description" :{
                                    "type": 'string', 
                                    "description": 'A short description of this emerging technology, in 10 to 30 words.'
                                },
                                "relevancy" :{
                                    "type": 'integer', 
                                    "description": 'Your appreciation of the relevancy and importance of the technology. 0 is really weak, 5 is strong and shouldnt be missed.'
                                }                                
                            },
                            "required": ["name","description","relevancy"],
                        }
                    },
                },
                "required": ["technology"],
            },
        }
    ]
    return functions




def getEmergingBehaviors():
    functions = [
            {
            "name": "get_emergingbehaviors",
            "description": "If the user asks for emerging behaviors, act like a Futurist, process the text and extract if you can a list of emerging behaviors. Do not invent anything, stick to what is explicitly detailed or can be inferred directly from the text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "behaviors": {
                        "type": 'array',
                        "items": {
                            "type": 'object',
                            "description": "An emerging behavior, as you have identified.",
                            "properties": {
                                "name" :{
                                    "type": 'string', 
                                    "description": 'A name for this emerging behavior'
                                },
                                "description" :{
                                    "type": 'string', 
                                    "description": 'A short description of this emerging behavior, in 10 to 30 words.'
                                },
                                "relevancy" :{
                                    "type": 'integer', 
                                    "description": 'Your appreciation of the relevancy and importance of the behavior. 0 is really weak, 5 is strong and shouldnt be missed.'
                                }                                
                            },
                            "required": ["name","description","relevancy"],
                        }
                    },
                },
                "required": ["behaviors"],
            },
        }
    ]
    return functions