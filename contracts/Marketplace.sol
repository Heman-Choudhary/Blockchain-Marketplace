// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Marketplace {
    struct Product {
        uint id;
        string name;
        uint price;
        address payable seller;
        address buyer;
        bool isSold;
    }

    Product[] public products;
    mapping(address => uint[]) public userPurchases;

    event ProductCreated(uint id, string name, uint price, address seller);
    event ProductPurchased(uint id, address buyer);

    // Create a new product
    function createProduct(string memory _name, uint _price) public {
        require(bytes(_name).length > 0, "Product name required");
        require(_price > 0, "Price must be greater than zero");

        products.push(Product({
            id: products.length,
            name: _name,
            price: _price,
            seller: payable(msg.sender),
            buyer: address(0),
            isSold: false
        }));

        emit ProductCreated(products.length - 1, _name, _price, msg.sender);
    }

    // Purchase a product
    function purchaseProduct(uint _id) public payable {
        require(_id < products.length, "Invalid product ID");
        Product storage product = products[_id];
        require(!product.isSold, "Product already sold");
        require(msg.value == product.price, "Incorrect ETH amount");

        product.seller.transfer(msg.value);
        product.buyer = msg.sender;
        product.isSold = true;

        userPurchases[msg.sender].push(_id);

        emit ProductPurchased(_id, msg.sender);
    }

    // Get all available (unsold) products
    function getAvailableProducts() public view returns (
        uint[] memory, string[] memory, uint[] memory, address[] memory
    ) {
        uint availableCount = 0;
        for (uint i = 0; i < products.length; i++) {
            if (!products[i].isSold) {
                availableCount++;
            }
        }

        uint[] memory ids = new uint[](availableCount);
        string[] memory names = new string[](availableCount);
        uint[] memory prices = new uint[](availableCount);
        address[] memory sellers = new address[](availableCount);

        uint index = 0;
        for (uint i = 0; i < products.length; i++) {
            if (!products[i].isSold) {
                ids[index] = products[i].id;
                names[index] = products[i].name;
                prices[index] = products[i].price;
                sellers[index] = products[i].seller;
                index++;
            }
        }

        return (ids, names, prices, sellers);
    }

    // Get products purchased by the caller
    function getMyPurchases() public view returns (Product[] memory) {
        uint[] memory purchaseIds = userPurchases[msg.sender];
        Product[] memory myProducts = new Product[](purchaseIds.length);

        for (uint i = 0; i < purchaseIds.length; i++) {
            myProducts[i] = products[purchaseIds[i]];
        }

        return myProducts;
    }

    // Get a product by its ID
    function getProductById(uint _id) public view returns (Product memory) {
        require(_id < products.length, "Invalid product ID");
        return products[_id];
    }
}
