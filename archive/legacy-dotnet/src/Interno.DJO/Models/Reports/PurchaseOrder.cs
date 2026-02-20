using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class PurchaseOrder
    {

        public string ShipTo { get; set; }
        public int PO { get; set; }
        public int Rel { get; set; }
        public int Line { get; set; }
        public int Ship { get; set; }
        public string Item { get; set; }
        public string SupItem { get; set; }
        public string Supplier { get; set; }
        public decimal QtyOrd { get; set; }
        public decimal QtyRec { get; set; }
        public decimal QtyBilled { get; set; }
        public decimal QtyDue { get; set; }
        public decimal QtyCancelled { get; set; }
        public DateTime? Promised { get; set; }
        public DateTime NeedBy { get; set; }
        public DateTime OrderDate { get; set; }
        public string Buyer { get; set; }
        public string Status { get; set; }
        public string AuthorizationStatus { get; set; }
        public decimal Price { get; set; }
        public decimal ShpAmount { get; set; }
        public string UOM { get; set; }
        public string Site { get; set; }
        public string Curr { get; set; }
        public string CountryOfOrigen { get; set; }
        public string ReceiptRouting { get; set; }
    }
}