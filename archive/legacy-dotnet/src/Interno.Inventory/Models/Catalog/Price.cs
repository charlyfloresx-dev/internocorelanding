using System;
using Interno.Common.Models; 

namespace Interno.Inventory.Domain.Entities
{
    public class ProductPrice : MultiTenantBase // company_id obligatorio
    {
        public int Id { get; set; }
        public Guid Guid { get; set; }
        public Guid ProductId { get; set; }
        
        // Relación con el almacén (Warehouse)
        // Si es null, podría considerarse un precio "Global" de la empresa
        public Guid? WarehouseId { get; set; } 

        public decimal PurchaseCost { get; set; }  
        public decimal AverageCost { get; set; }   
        public decimal SellingPrice { get; set; }  
        public decimal TransferPrice { get; set; } 

        public PriceType Type { get; set; } 
        public string CurrencyCode { get; set; } 
        
        public DateTime EffectiveDate { get; set; }
        public bool IsActive { get; set; }

        public int? PartnershipId { get; set; }
        public Interno.Inventory.Models.Partnership Partnership { get; set; }
    }
}