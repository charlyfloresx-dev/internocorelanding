
using System.ComponentModel.DataAnnotations;
namespace Interno.Domain.Catalog
{
    public class Autority
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        [MaxLength(45)]
        public string Name { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
        [MaxLength(45)]
        public string Type { get; set; } //Company - Hospital - Warehouse
    }
}