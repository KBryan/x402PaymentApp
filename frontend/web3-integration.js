/**
 * Web3 Integration Module
 * Handles wallet connectivity and blockchain interactions
 */

class Web3Integration {
    constructor() {
        this.web3 = null;
        this.account = null;
        this.isConnected = false;
        this.chainId = null;
        this.contractAddress = null;
        this.contractABI = null;
        this.contract = null;
        
        // Event listeners
        this.onAccountChange = null;
        this.onChainChange = null;
        this.onConnect = null;
        this.onDisconnect = null;
        
        this.init();
    }
    
    async init() {
        // Check if MetaMask is installed
        if (typeof window.ethereum !== 'undefined') {
            this.web3 = new Web3(window.ethereum);
            
            // Listen for account changes
            window.ethereum.on('accountsChanged', (accounts) => {
                this.handleAccountsChanged(accounts);
            });
            
            // Listen for chain changes
            window.ethereum.on('chainChanged', (chainId) => {
                this.handleChainChanged(chainId);
            });
            
            // Check if already connected
            try {
                const accounts = await window.ethereum.request({ method: 'eth_accounts' });
                if (accounts.length > 0) {
                    this.account = accounts[0];
                    this.isConnected = true;
                    this.chainId = await window.ethereum.request({ method: 'eth_chainId' });
                    if (this.onConnect) this.onConnect(this.account);
                }
            } catch (error) {
                console.error('Error checking existing connection:', error);
            }
        } else {
            console.warn('MetaMask not detected');
        }
    }
    
    async connectWallet() {
        if (!window.ethereum) {
            throw new Error('MetaMask not installed. Please install MetaMask to continue.');
        }
        
        try {
            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });
            
            if (accounts.length > 0) {
                this.account = accounts[0];
                this.isConnected = true;
                this.chainId = await window.ethereum.request({ method: 'eth_chainId' });
                
                if (this.onConnect) this.onConnect(this.account);
                
                return {
                    success: true,
                    account: this.account,
                    chainId: this.chainId
                };
            } else {
                throw new Error('No accounts found');
            }
        } catch (error) {
            console.error('Error connecting wallet:', error);
            throw error;
        }
    }
    
    async disconnectWallet() {
        this.account = null;
        this.isConnected = false;
        this.chainId = null;
        
        if (this.onDisconnect) this.onDisconnect();
        
        return { success: true };
    }
    
    handleAccountsChanged(accounts) {
        if (accounts.length === 0) {
            // User disconnected
            this.disconnectWallet();
        } else if (accounts[0] !== this.account) {
            // User switched accounts
            this.account = accounts[0];
            if (this.onAccountChange) this.onAccountChange(this.account);
        }
    }
    
    handleChainChanged(chainId) {
        this.chainId = chainId;
        if (this.onChainChange) this.onChainChange(chainId);
        
        // Reload the page to reset the dapp state
        window.location.reload();
    }
    
    getAccount() {
        return this.account;
    }
    
    getChainId() {
        return this.chainId;
    }
    
    isWalletConnected() {
        return this.isConnected && this.account;
    }
    
    formatAddress(address) {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }
    
    async getBalance(address = null) {
        if (!this.web3) throw new Error('Web3 not initialized');
        
        const targetAddress = address || this.account;
        if (!targetAddress) throw new Error('No address provided');
        
        try {
            const balance = await this.web3.eth.getBalance(targetAddress);
            return this.web3.utils.fromWei(balance, 'ether');
        } catch (error) {
            console.error('Error getting balance:', error);
            throw error;
        }
    }
    
    async sendTransaction(to, value, data = '0x') {
        if (!this.isConnected) throw new Error('Wallet not connected');
        
        try {
            const transactionParameters = {
                to: to,
                from: this.account,
                value: this.web3.utils.toHex(this.web3.utils.toWei(value.toString(), 'ether')),
                data: data,
            };
            
            const txHash = await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [transactionParameters],
            });
            
            return txHash;
        } catch (error) {
            console.error('Error sending transaction:', error);
            throw error;
        }
    }
    
    async signMessage(message) {
        if (!this.isConnected) throw new Error('Wallet not connected');
        
        try {
            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [message, this.account],
            });
            
            return signature;
        } catch (error) {
            console.error('Error signing message:', error);
            throw error;
        }
    }
    
    async switchToChain(chainId) {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: chainId }],
            });
        } catch (switchError) {
            // This error code indicates that the chain has not been added to MetaMask
            if (switchError.code === 4902) {
                throw new Error('Chain not added to MetaMask');
            }
            throw switchError;
        }
    }
    
    async addChain(chainConfig) {
        try {
            await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [chainConfig],
            });
        } catch (error) {
            console.error('Error adding chain:', error);
            throw error;
        }
    }
    
    // Contract interaction methods
    setContract(address, abi) {
        if (!this.web3) throw new Error('Web3 not initialized');
        
        this.contractAddress = address;
        this.contractABI = abi;
        this.contract = new this.web3.eth.Contract(abi, address);
    }
    
    async callContractMethod(methodName, params = [], options = {}) {
        if (!this.contract) throw new Error('Contract not set');
        
        try {
            const method = this.contract.methods[methodName](...params);
            
            if (options.send) {
                // Send transaction
                const gasEstimate = await method.estimateGas({ from: this.account });
                const result = await method.send({
                    from: this.account,
                    gas: gasEstimate,
                    ...options
                });
                return result;
            } else {
                // Call method (read-only)
                const result = await method.call({ from: this.account });
                return result;
            }
        } catch (error) {
            console.error(`Error calling contract method ${methodName}:`, error);
            throw error;
        }
    }
    
    // Utility methods
    toWei(amount, unit = 'ether') {
        if (!this.web3) throw new Error('Web3 not initialized');
        return this.web3.utils.toWei(amount.toString(), unit);
    }
    
    fromWei(amount, unit = 'ether') {
        if (!this.web3) throw new Error('Web3 not initialized');
        return this.web3.utils.fromWei(amount.toString(), unit);
    }
    
    isValidAddress(address) {
        if (!this.web3) return false;
        return this.web3.utils.isAddress(address);
    }
    
    // Event listeners
    onWalletConnect(callback) {
        this.onConnect = callback;
    }
    
    onWalletDisconnect(callback) {
        this.onDisconnect = callback;
    }
    
    onAccountChanged(callback) {
        this.onAccountChange = callback;
    }
    
    onChainChanged(callback) {
        this.onChainChange = callback;
    }
}

// SKALE Chain configurations
const SKALE_CHAINS = {
    testnet: {
        chainId: '0x561bf78b', // SKALE Calypso Hub Testnet
        chainName: 'SKALE Calypso Hub Testnet',
        nativeCurrency: {
            name: 'sFUEL',
            symbol: 'sFUEL',
            decimals: 18
        },
        rpcUrls: ['https://testnet.skalenodes.com/v1/giant-half-dual-testnet'],
        blockExplorerUrls: ['https://giant-half-dual-testnet.explorer.testnet.skalenodes.com']
    },
    mainnet: {
        chainId: '0x561bf78a', // SKALE Calypso Hub
        chainName: 'SKALE Calypso Hub',
        nativeCurrency: {
            name: 'sFUEL',
            symbol: 'sFUEL',
            decimals: 18
        },
        rpcUrls: ['https://mainnet.skalenodes.com/v1/honorable-steel-rasalhague'],
        blockExplorerUrls: ['https://honorable-steel-rasalhague.explorer.mainnet.skalenodes.com']
    }
};

// Payment signature helper
class PaymentSigner {
    constructor(web3Integration) {
        this.web3 = web3Integration;
    }
    
    async createPaymentSignature(planId, amount, token, timestamp) {
        if (!this.web3.isWalletConnected()) {
            throw new Error('Wallet not connected');
        }
        
        const message = {
            planId: planId,
            amount: amount.toString(),
            token: token,
            timestamp: timestamp,
            from: this.web3.getAccount()
        };
        
        const messageString = JSON.stringify(message);
        const signature = await this.web3.signMessage(messageString);
        
        return {
            message: message,
            signature: signature,
            messageString: messageString
        };
    }
    
    createPaymentHeader(paymentData) {
        const payload = {
            amount: paymentData.amount,
            token: paymentData.token,
            signature: paymentData.signature,
            timestamp: paymentData.timestamp,
            from_address: paymentData.from_address || this.web3.getAccount(),
            transaction_hash: paymentData.transaction_hash || ''
        };
        
        return btoa(JSON.stringify(payload));
    }
}

// Export for use in other modules
window.Web3Integration = Web3Integration;
window.PaymentSigner = PaymentSigner;
window.SKALE_CHAINS = SKALE_CHAINS;

