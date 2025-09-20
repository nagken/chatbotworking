// Simple test to add to browser console
// This will help us debug the streaming issue

console.log('🧪 Starting streaming debug test...');

async function testStreamingInBrowser() {
    const message = "How do I process a prescription refill for a member?";
    
    try {
        console.log('📡 Sending streaming request...');
        
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
                // Note: Using current session, no explicit auth header needed
            },
            body: JSON.stringify({
                message: message,
                conversation_id: null
            })
        });
        
        console.log('📊 Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Request failed:', errorText);
            return;
        }
        
        console.log('🌊 Reading stream...');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let messageCount = 0;
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                console.log('✅ Stream completed');
                break;
            }
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    messageCount++;
                    const data = JSON.parse(line.substring(6));
                    console.log(`📦 Message ${messageCount}:`, data);
                    
                    if (data.type === 'system_message' && data.message_type === 'text_response') {
                        console.log('💬 Text content:', data.data.content);
                        
                        if (data.data.is_final) {
                            console.log('🎉 Final response received!');
                            console.log('📝 Complete response:', data.data.content);
                            break;
                        }
                    }
                }
            }
        }
        
        console.log(`✅ Test completed. Total messages: ${messageCount}`);
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    }
}

// Run the test
testStreamingInBrowser();
