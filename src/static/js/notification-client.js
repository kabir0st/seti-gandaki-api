/**
 * Notification WebSocket Client
 * 
 * This client connects to the WebSocket server and handles notifications.
 * It can be included in frontend applications to receive real-time notifications.
 */

class NotificationClient {
    /**
     * Create a new NotificationClient
     * 
     * @param {string} token - The authentication token
     * @param {Object} options - Configuration options
     * @param {string} options.wsUrl - WebSocket URL (default: derived from current location)
     * @param {Function} options.onNotification - Callback for new notifications
     * @param {Function} options.onConnect - Callback when connection is established
     * @param {Function} options.onDisconnect - Callback when connection is closed
     * @param {Function} options.onError - Callback for errors
     */
    constructor(token, options = {}) {
        this.token = token;
        this.options = options;
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectInterval = options.reconnectInterval || 3000;

        // Default WebSocket URL if not provided
        if (!options.wsUrl) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            this.wsUrl = `${protocol}//${host}/ws/global/`;
        } else {
            this.wsUrl = options.wsUrl;
        }
    }

    /**
     * Connect to the WebSocket server
     */
    connect() {
        if (this.socket) {
            this.disconnect();
        }

        try {
            this.socket = new WebSocket(this.wsUrl);

            this.socket.onopen = (event) => {
                console.log('WebSocket connection established');
                this.connected = true;
                this.reconnectAttempts = 0;

                // Send authorization header
                this.socket.send(JSON.stringify({
                    authorization: this.token
                }));

                if (this.options.onConnect) {
                    this.options.onConnect(event);
                }
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    // Handle notification messages
                    if (data.id && data.msg) {
                        if (this.options.onNotification) {
                            this.options.onNotification(data);
                        }
                    } else {
                        console.log('Received message:', data);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.socket.onclose = (event) => {
                console.log('WebSocket connection closed');
                this.connected = false;

                if (this.options.onDisconnect) {
                    this.options.onDisconnect(event);
                }

                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                    setTimeout(() => this.connect(), this.reconnectInterval);
                }
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);

                if (this.options.onError) {
                    this.options.onError(error);
                }
            };
        } catch (error) {
            console.error('Error creating WebSocket connection:', error);

            if (this.options.onError) {
                this.options.onError(error);
            }
        }
    }

    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.connected = false;
        }
    }

    /**
     * Mark notifications as read
     * 
     * @param {Array<number>} notificationIds - Array of notification IDs to mark as read
     * @returns {Promise} - Promise that resolves when the operation is complete
     */
    markAsRead(notificationIds) {
        if (!this.connected) {
            return Promise.reject(new Error('WebSocket not connected'));
        }

        return new Promise((resolve, reject) => {
            try {
                const message = {
                    event: 'notification_read',
                    notification_ids: notificationIds
                };

                this.socket.send(JSON.stringify(message));
                resolve();
            } catch (error) {
                reject(error);
            }
        });
    }
}

// Export for use in module systems
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = NotificationClient;
} else {
    window.NotificationClient = NotificationClient;
}