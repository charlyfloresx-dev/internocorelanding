using System;
namespace Interno.Inventory
{
    public class ExchangeRate
    {
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public Interno.Domain.Catalog.Currency From { get; set; }
        public Interno.Domain.Catalog.Currency To { get; set; }
        public decimal Value { get; set; }
    }
}