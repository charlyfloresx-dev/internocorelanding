using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Http;

namespace Interno.Inventory.Models
{
    public class Document
    {
        [KeyAttribute]
        public int Id { get; set; }
        [Required]
        public Concept Concept { get; set; }
        [Required]
        public ConceptType ConceptType { get; set; }
        
        [Required]
        public Partnership Partnership { get; set; }
        [Required]
        public Warehouse Warehouse { get; set; }

        [DataType(DataType.DateTime)]
        public DateTime DeliveryDate { get; set; } //Entrega

        // Cuantity - Payment
        public Interno.Domain.Catalog.Currency Currency { get; set; }
        public float SubTotal { get; set; }
        public float Tax { get; set; }
        public float Units { get; set; }
        public float Discount { get; set; }
        public float Total{ get; set; }
        public Interno.Domain.Catalog.Payment PaymentMethod { get; set; }

        // References
        public string Series { get; set; }
        public string Sheet { get; set; } // Folio
        public string Reference { get; set; }
        public Document DocOfOrigen { get; set; }
        public string Observations { get; set; }
        public string TrackingNumber { get; set; }

        [Required]
        //public string CreateUser { get; set; } =  HttpContext.User.Identity.Name.Split("\\")[1];
        [TimestampAttribute]
        public DateTime CreateDate { get; set;}
        [DataType(DataType.DateTime)]
        public DateTime LastUpdate { get; set;}
        [Required]
        public Interno.Domain.Catalog.Location CurrentPlace { get; set; }
        public virtual ICollection<Interno.Inventory.Models.Movements> Movements { get; set; } = new List<Movements>();

    }
}